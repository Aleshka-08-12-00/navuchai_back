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
                completed_by=completed_by
            )
            db.add(status)
        await db.commit()
        return {"success": True}
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении статуса элемента: {str(e)}")


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
        return result.scalar_one()
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


