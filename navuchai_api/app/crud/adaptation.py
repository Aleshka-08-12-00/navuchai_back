from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.exceptions import DatabaseException, NotFoundException
from app.models import (
    AdaptationTemplate, AdaptationSection, AdaptationElement,
    EmployeeAdaptation, AdaptationElementStatus, User
)
from app.schemas.adaptation import (
    AdaptationTemplateCreate, AdaptationTemplate as AdaptationTemplateSchema,
    EmployeeAdaptationCreate, EmployeeAdaptation as EmployeeAdaptationSchema,
    AdaptationSectionCreate, AdaptationSectionUpdate,
    AdaptationElementCreate, AdaptationElementUpdate,
)

# Helpers to grant access for adaptation elements
async def _grant_access_for_element(db: AsyncSession, user_id: int, element: AdaptationElement):
    try:
        etype = (element.type or '').lower()
        if etype == 'text':
            return
        if etype == 'test' and element.entity_id:
            from app.crud.test_access import get_test_access, create_test_access
            from app.schemas.test_access import TestAccessCreate
            existing = await get_test_access(db, element.entity_id, user_id)
            if not existing:
                payload = TestAccessCreate(test_id=element.entity_id, user_id=user_id, status_id=1)
                await create_test_access(db, payload)
            return
        if etype == 'course' and element.entity_id:
            from app.crud.enrollment import enroll_user
            await enroll_user(db, element.entity_id, user_id)
            return
        if etype == 'module' and element.entity_id:
            from app.crud.module import get_module
            module = await get_module(db, element.entity_id)
            if getattr(module, 'course_id', None):
                from app.crud.enrollment import enroll_user
                await enroll_user(db, module.course_id, user_id)
            return
        if etype == 'lesson' and element.entity_id:
            from app.crud.lesson import get_lesson
            lesson = await get_lesson(db, element.entity_id)
            course_id = None
            if getattr(lesson, 'module', None) and getattr(lesson.module, 'course_id', None):
                course_id = lesson.module.course_id
            if course_id:
                from app.crud.enrollment import enroll_user
                await enroll_user(db, course_id, user_id)
            return
        # faq: нет отдельной выдачи доступа
    except Exception:
        # Не прерываем основную операцию, если выдача доступа не удалась
        pass


# Templates
async def get_templates(db: AsyncSession) -> list[AdaptationTemplate]:
    try:
        result = await db.execute(
            select(AdaptationTemplate)
            .options(selectinload(AdaptationTemplate.sections).selectinload(AdaptationSection.elements))
            .order_by(AdaptationTemplate.id)
        )
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении шаблонов: {str(e)}")


async def get_template(db: AsyncSession, template_id: int) -> AdaptationTemplate:
    try:
        result = await db.execute(
            select(AdaptationTemplate)
            .options(selectinload(AdaptationTemplate.sections).selectinload(AdaptationSection.elements))
            .where(AdaptationTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise NotFoundException("Шаблон не найден")
        return template
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении шаблона: {str(e)}")


async def create_template(db: AsyncSession, data: AdaptationTemplateCreate, creator_id: int) -> AdaptationTemplate:
    try:
        template = AdaptationTemplate(
            title=data.title,
            description=data.description,
            welcome_message=data.welcome_message,
            is_active=data.is_active if data.is_active is not None else True,
            creator_id=creator_id,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании шаблона: {str(e)}")


async def update_template(db: AsyncSession, template_id: int, data: AdaptationTemplateCreate) -> AdaptationTemplate:
    try:
        template = await get_template(db, template_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(template, field, value)
        await db.commit()
        await db.refresh(template)
        return template
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении шаблона: {str(e)}")


async def delete_template(db: AsyncSession, template_id: int) -> bool:
    try:
        template = await get_template(db, template_id)
        await db.delete(template)
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении шаблона: {str(e)}")


# Employee Adaptations
async def get_employee_adaptations(db: AsyncSession) -> list[EmployeeAdaptation]:
    try:
        result = await db.execute(
            select(EmployeeAdaptation)
            .options(selectinload(EmployeeAdaptation.template))
            .order_by(EmployeeAdaptation.id)
        )
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении адаптаций сотрудников: {str(e)}")


async def get_employee_adaptation(db: AsyncSession, adaptation_id: int) -> EmployeeAdaptation:
    try:
        result = await db.execute(
            select(EmployeeAdaptation)
            .options(selectinload(EmployeeAdaptation.template).selectinload(AdaptationTemplate.sections).selectinload(AdaptationSection.elements))
            .where(EmployeeAdaptation.id == adaptation_id)
        )
        adaptation = result.scalar_one_or_none()
        if not adaptation:
            raise NotFoundException("Адаптация не найдена")
        return adaptation
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении адаптации: {str(e)}")


async def assign_adaptation(db: AsyncSession, payload: EmployeeAdaptationCreate) -> EmployeeAdaptation:
    try:
        # ensure users exist
        for uid in [payload.employee_id, payload.assigned_by]:
            user = await db.execute(select(User).where(User.id == uid))
            if not user.scalar_one_or_none():
                raise NotFoundException(f"Пользователь {uid} не найден")

        adaptation = EmployeeAdaptation(
            template_id=payload.template_id,
            employee_id=payload.employee_id,
            assigned_by=payload.assigned_by,
        )
        db.add(adaptation)
        await db.commit()
        await db.refresh(adaptation)

        # Выдать доступы по элементам шаблона (кроме текста)
        tpl_q = await db.execute(
            select(AdaptationTemplate)
            .options(selectinload(AdaptationTemplate.sections).selectinload(AdaptationSection.elements))
            .where(AdaptationTemplate.id == payload.template_id)
        )
        template = tpl_q.scalar_one_or_none()
        if template:
            for section in template.sections:
                for el in section.elements:
                    await _grant_access_for_element(db, payload.employee_id, el)
        return adaptation
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при назначении адаптации: {str(e)}")


async def delete_employee_adaptation(db: AsyncSession, adaptation_id: int) -> bool:
    try:
        adaptation = await get_employee_adaptation(db, adaptation_id)
        await db.delete(adaptation)
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении адаптации: {str(e)}")


# Element status
async def update_element_status(db: AsyncSession, element_id: int, employee_adaptation_id: int, is_completed: bool, completed_by: int) -> dict:
    try:
        # upsert by unique (employee_adaptation_id, element_id)
        result = await db.execute(
            select(AdaptationElementStatus).where(
                AdaptationElementStatus.employee_adaptation_id == employee_adaptation_id,
                AdaptationElementStatus.element_id == element_id
            )
        )
        status = result.scalar_one_or_none()
        if status:
            status.is_completed = is_completed
            status.completed_by = completed_by
        else:
            status = AdaptationElementStatus(
                employee_adaptation_id=employee_adaptation_id,
                element_id=element_id,
                is_completed=is_completed,
                completed_by=completed_by  # Используем переданное значение или null
            )
            db.add(status)
        await db.commit()
        
        # Проверяем и обновляем статус адаптации
        await _check_and_update_adaptation_completion(db, employee_adaptation_id)
        await db.commit()
        
        return {"success": True}
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении статуса элемента: {str(e)}")


async def _check_and_update_adaptation_completion(db: AsyncSession, adaptation_id: int):
    """Проверяет и обновляет статус завершения адаптации на основе статусов элементов"""
    try:
        # Получаем адаптацию
        adaptation_result = await db.execute(
            select(EmployeeAdaptation).where(EmployeeAdaptation.id == adaptation_id)
        )
        adaptation = adaptation_result.scalar_one_or_none()
        if not adaptation:
            return

        # Получаем все элементы шаблона
        elements_result = await db.execute(
            select(AdaptationElement)
            .join(AdaptationSection)
            .join(AdaptationTemplate)
            .where(AdaptationTemplate.id == adaptation.template_id)
        )
        all_elements = elements_result.scalars().all()
        
        if not all_elements:
            return

        # Получаем статусы элементов для этой адаптации
        statuses_result = await db.execute(
            select(AdaptationElementStatus)
            .where(AdaptationElementStatus.employee_adaptation_id == adaptation_id)
        )
        element_statuses = statuses_result.scalars().all()
        
        # Создаем словарь статусов по element_id
        status_by_element = {status.element_id: status.is_completed for status in element_statuses}
        
        # Проверяем, все ли элементы завершены
        all_completed = True
        for element in all_elements:
            if element.id not in status_by_element or not status_by_element[element.id]:
                all_completed = False
                break
        
        # Обновляем статус адаптации
        if all_completed and not adaptation.is_completed:
            adaptation.is_completed = True
            adaptation.completion_percentage = 100.0
            if not adaptation.completed_at:
                from datetime import datetime
                adaptation.completed_at = datetime.utcnow()
        elif not all_completed and adaptation.is_completed:
            adaptation.is_completed = False
            # Пересчитываем процент завершения
            completed_count = sum(1 for status in element_statuses if status.is_completed)
            adaptation.completion_percentage = (completed_count / len(all_elements)) * 100.0
            adaptation.completed_at = None
            
    except Exception:
        # Не прерываем основную операцию при ошибке проверки
        pass


async def bulk_update_element_statuses(db: AsyncSession, updates: List[dict], user_id: int) -> List[AdaptationElementStatus]:
    """Массовое обновление статусов элементов адаптации для конкретного пользователя"""
    try:
        updated_statuses = []
        affected_adaptations = set()
        
        for update in updates:
            element_id = update.get('element_id')
            is_completed = update.get('is_completed')
            
            if element_id is None or is_completed is None:
                continue
                
            # Получаем элемент
            element_result = await db.execute(
                select(AdaptationElement).where(AdaptationElement.id == element_id)
            )
            element = element_result.scalar_one_or_none()
            if not element:
                continue
                
            # Получаем адаптации только для текущего пользователя
            adaptations_result = await db.execute(
                select(EmployeeAdaptation)
                .join(AdaptationTemplate)
                .join(AdaptationSection)
                .join(AdaptationElement)
                .where(
                    AdaptationElement.id == element_id,
                    EmployeeAdaptation.employee_id == user_id
                )
            )
            adaptations = adaptations_result.scalars().all()
            
            for adaptation in adaptations:
                # Проверяем существующий статус
                status_result = await db.execute(
                    select(AdaptationElementStatus)
                    .where(
                        AdaptationElementStatus.employee_adaptation_id == adaptation.id,
                        AdaptationElementStatus.element_id == element_id
                    )
                )
                status = status_result.scalar_one_or_none()
                
                if not status:
                    # Создаем новый статус
                    status = AdaptationElementStatus(
                        employee_adaptation_id=adaptation.id,
                        element_id=element_id,
                        is_completed=is_completed,
                        completed_by=user_id  # Используем ID текущего пользователя
                    )
                    db.add(status)
                else:
                    # Обновляем существующий статус
                    status.is_completed = is_completed
                    if is_completed and not status.completed_by:
                        status.completed_by = user_id
                
                updated_statuses.append(status)
                affected_adaptations.add(adaptation.id)
        
        await db.commit()
        
        # Проверяем и обновляем статусы адаптаций
        for adaptation_id in affected_adaptations:
            await _check_and_update_adaptation_completion(db, adaptation_id)
        
        await db.commit()
        return updated_statuses
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при массовом обновлении статусов: {str(e)}")


# Stats and progress
async def get_stats(db: AsyncSession) -> dict:
    try:
        tpl_q = await db.execute(select(AdaptationTemplate))
        ad_q = await db.execute(select(EmployeeAdaptation))
        return {
            "total_templates": len(tpl_q.scalars().all()),
            "total_adaptations": len(ad_q.scalars().all()),
        }
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении статистики: {str(e)}")


async def get_progress(db: AsyncSession, adaptation_id: int) -> list[dict]:
    """Возвращает прогресс по секциям для указанной адаптации сотрудника."""
    try:
        # Адаптация с деревом шаблона
        result = await db.execute(
            select(EmployeeAdaptation)
            .options(
                selectinload(EmployeeAdaptation.template)
                .selectinload(AdaptationTemplate.sections)
                .selectinload(AdaptationSection.elements)
            )
            .where(EmployeeAdaptation.id == adaptation_id)
        )
        adaptation = result.scalar_one_or_none()
        if not adaptation:
            raise NotFoundException("Адаптация не найдена")

        # Статусы элементов по адаптации
        statuses_q = await db.execute(
            select(AdaptationElementStatus).where(
                AdaptationElementStatus.employee_adaptation_id == adaptation_id
            )
        )
        statuses = statuses_q.scalars().all()
        status_by_element: dict[int, AdaptationElementStatus] = {
            s.element_id: s for s in statuses
        }

        progress: list[dict] = []
        for section in adaptation.template.sections:
            total = len(section.elements)
            completed = 0
            elements_detail: list[dict] = []
            for el in section.elements:
                st = status_by_element.get(el.id)
                is_completed = bool(st.is_completed) if st else bool(el.is_completed)
                if is_completed:
                    completed += 1
                elements_detail.append({
                    "element_id": el.id,
                    "title": el.title,
                    "type": el.type,
                    "is_completed": is_completed,
                    "completed_at": getattr(st, 'completed_at', None) if st else el.completed_at,
                })

            percent = round((completed / total) * 100) if total else 0
            progress.append({
                "section_id": section.id,
                "section_title": section.title,
                "total": total,
                "completed": completed,
                "percent": percent,
                "elements": elements_detail,
            })

        return progress
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении прогресса: {str(e)}")


async def copy_adaptation(db: AsyncSession, source_adaptation_id: int, target_employee_id: int) -> EmployeeAdaptation:
    try:
        source = await get_employee_adaptation(db, source_adaptation_id)
        new = EmployeeAdaptation(
            template_id=source.template_id,
            employee_id=target_employee_id,
            assigned_by=source.assigned_by,
        )
        db.add(new)
        await db.commit()
        await db.refresh(new)
        return new
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при копировании адаптации: {str(e)}")


# User adaptations
async def get_user_adaptations(db: AsyncSession, user_id: int) -> list[dict]:
    """Получить все адаптации пользователя с полной структурой шаблона."""
    try:
        result = await db.execute(
            select(EmployeeAdaptation)
            .options(
                selectinload(EmployeeAdaptation.template)
                .selectinload(AdaptationTemplate.sections)
                .selectinload(AdaptationSection.elements)
            )
            .where(EmployeeAdaptation.employee_id == user_id)
            .order_by(EmployeeAdaptation.assigned_at.desc())
        )
        adaptations = result.scalars().all()
        
        # Статусы элементов для всех адаптаций
        adaptation_ids = [a.id for a in adaptations]
        statuses_q = await db.execute(
            select(AdaptationElementStatus).where(
                AdaptationElementStatus.employee_adaptation_id.in_(adaptation_ids)
            )
        )
        statuses = statuses_q.scalars().all()
        status_by_adaptation_element: dict[tuple[int, int], AdaptationElementStatus] = {
            (s.employee_adaptation_id, s.element_id): s for s in statuses
        }
        
        user_adaptations = []
        for adaptation in adaptations:
            sections_data = []
            for section in adaptation.template.sections:
                elements_data = []
                for element in section.elements:
                    status = status_by_adaptation_element.get((adaptation.id, element.id))
                    is_completed = bool(status.is_completed) if status else bool(element.is_completed)
                    elements_data.append({
                        "element_id": element.id,
                        "title": element.title,
                        "description": element.description,
                        "type": element.type,
                        "text_content": element.text_content,
                        "entity_type": element.entity_type,
                        "entity_id": element.entity_id,
                        "entity_title": element.entity_title,
                        "is_completed": is_completed,
                        "completed_at": getattr(status, 'completed_at', None) if status else element.completed_at,
                        "order_index": element.order_index,
                        "parent_id": element.parent_id,
                        "level": element.level,
                    })
                
                sections_data.append({
                    "section_id": section.id,
                    "title": section.title,
                    "description": section.description,
                    "icon": section.icon,
                    "order_index": section.order_index,
                    "elements": elements_data,
                })
            
            user_adaptations.append({
                "adaptation_id": adaptation.id,
                "template_id": adaptation.template_id,
                "template_title": adaptation.template.title,
                "is_completed": adaptation.is_completed,
                "completion_percentage": adaptation.completion_percentage,
                "assigned_at": adaptation.assigned_at,
                "started_at": adaptation.started_at,
                "completed_at": adaptation.completed_at,
                "created_at": adaptation.created_at,
                "updated_at": adaptation.updated_at,
                "sections": sections_data,
            })
        
        return user_adaptations
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении адаптаций пользователя: {str(e)}")


async def update_user_adaptation(db: AsyncSession, user_id: int, adaptation_id: int, data: dict) -> EmployeeAdaptation:
    """Обновить адаптацию пользователя."""
    try:
        result = await db.execute(
            select(EmployeeAdaptation).where(
                EmployeeAdaptation.id == adaptation_id,
                EmployeeAdaptation.employee_id == user_id
            )
        )
        adaptation = result.scalar_one_or_none()
        if not adaptation:
            raise NotFoundException("Адаптация не найдена")
        
        for field, value in data.items():
            if hasattr(adaptation, field):
                # Конвертируем timezone-aware datetime в naive для БД
                if field in ['started_at', 'completed_at'] and value is not None:
                    if hasattr(value, 'tzinfo') and value.tzinfo is not None:
                        value = value.replace(tzinfo=None)
                setattr(adaptation, field, value)
        
        await db.commit()
        await db.refresh(adaptation)
        return adaptation
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении адаптации: {str(e)}")


# Sections
async def create_section(db: AsyncSession, data: AdaptationSectionCreate):
    try:
        section = AdaptationSection(
            template_id=data.template_id,
            title=data.title,
            description=data.description,
            icon=data.icon,
            order_index=data.order_index,
        )
        db.add(section)
        await db.commit()
        # Возвращаем секцию с элементами (selectinload) для избежания MissingGreenlet
        result = await db.execute(
            select(AdaptationSection)
            .options(selectinload(AdaptationSection.elements))
            .where(AdaptationSection.id == section.id)
        )
        return result.scalar_one()
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании секции: {str(e)}")


async def update_section(db: AsyncSession, section_id: int, data: AdaptationSectionUpdate):
    try:
        result = await db.execute(select(AdaptationSection).where(AdaptationSection.id == section_id))
        section = result.scalar_one_or_none()
        if not section:
            raise NotFoundException("Секция не найдена")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(section, field, value)
        await db.commit()
        result = await db.execute(
            select(AdaptationSection)
            .options(selectinload(AdaptationSection.elements))
            .where(AdaptationSection.id == section.id)
        )
        return result.scalar_one()
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении секции: {str(e)}")


async def delete_section(db: AsyncSession, section_id: int) -> bool:
    try:
        result = await db.execute(select(AdaptationSection).where(AdaptationSection.id == section_id))
        section = result.scalar_one_or_none()
        if not section:
            raise NotFoundException("Секция не найдена")
        await db.delete(section)
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении секции: {str(e)}")


# Elements
async def create_element(db: AsyncSession, data: AdaptationElementCreate):
    try:
        element = AdaptationElement(
            section_id=data.section_id,
            title=data.title,
            description=data.description,
            type=data.type,
            text_content=data.text_content,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            entity_title=data.entity_title,
            order_index=data.order_index,
            parent_id=data.parent_id,
            level=data.level,
            completed_by=None,
        )
        db.add(element)
        await db.commit()
        # Возвращаем элемент без ленивых обращений к БД
        result = await db.execute(
            select(AdaptationElement).where(AdaptationElement.id == element.id)
        )
        created = result.scalar_one()

        # Выдать доступ пользователю(ям), у кого назначена адаптация с этим шаблоном
        tpl_id_q = await db.execute(
            select(AdaptationSection.template_id).where(AdaptationSection.id == created.section_id)
        )
        tpl_id = tpl_id_q.scalar_one_or_none()
        if tpl_id is not None:
            user_ids_q = await db.execute(
                select(EmployeeAdaptation.employee_id).where(EmployeeAdaptation.template_id == tpl_id)
            )
            for (uid,) in user_ids_q.all():
                await _grant_access_for_element(db, uid, created)
        return created
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании элемента: {str(e)}")


async def update_element(db: AsyncSession, element_id: int, data: AdaptationElementUpdate):
    try:
        result = await db.execute(select(AdaptationElement).where(AdaptationElement.id == element_id))
        element = result.scalar_one_or_none()
        if not element:
            raise NotFoundException("Элемент не найден")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(element, field, value)
        await db.commit()
        result = await db.execute(
            select(AdaptationElement).where(AdaptationElement.id == element.id)
        )
        return result.scalar_one()
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении элемента: {str(e)}")


async def delete_element(db: AsyncSession, element_id: int) -> bool:
    try:
        result = await db.execute(select(AdaptationElement).where(AdaptationElement.id == element_id))
        element = result.scalar_one_or_none()
        if not element:
            raise NotFoundException("Элемент не найден")
        await db.delete(element)
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении элемента: {str(e)}")


