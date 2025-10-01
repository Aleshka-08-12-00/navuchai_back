from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.exceptions import DatabaseException, NotFoundException
from app.schemas.adaptation import (
    AdaptationTemplate as AdaptationTemplateSchema,
    AdaptationTemplateCreate,
    EmployeeAdaptation as EmployeeAdaptationSchema,
    EmployeeAdaptationCreate,
    UpdateElementStatusRequest,
    CopyAdaptationRequest,
    AdaptationSection as AdaptationSectionSchema,
    AdaptationSectionCreate, AdaptationSectionUpdate,
    AdaptationElement as AdaptationElementSchema,
    AdaptationElementCreate, AdaptationElementUpdate,
    UserAdaptationProgress,
    UpdateAdaptationRequest,
)
from app.crud.adaptation import (
    get_templates, get_template, create_template, update_template, delete_template,
    get_employee_adaptations, get_employee_adaptation, assign_adaptation, delete_employee_adaptation,
    update_element_status, get_stats, get_progress, copy_adaptation,
    create_section, update_section, delete_section,
    create_element, update_element, delete_element,
    get_user_adaptations, update_user_adaptation,
)
from app.routes.auth import authorized_required


router = APIRouter(prefix="/api/adaptation", tags=["Adaptation"])


@router.get("/templates/", response_model=list[AdaptationTemplateSchema])
async def list_templates(db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await get_templates(db)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/{template_id}/", response_model=AdaptationTemplateSchema)
async def read_template(template_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await get_template(db, template_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/templates/", response_model=AdaptationTemplateSchema)
async def create_template_route(data: AdaptationTemplateCreate, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await create_template(db, data, creator_id=user.id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/templates/{template_id}/", response_model=AdaptationTemplateSchema)
async def update_template_route(template_id: int, data: AdaptationTemplateCreate, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await update_template(db, template_id, data)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/templates/{template_id}/", response_model=dict)
async def delete_template_route(template_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        ok = await delete_template(db, template_id)
        return {"success": bool(ok)}
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


# Employee adaptations
@router.get("/employee-adaptations/", response_model=list[EmployeeAdaptationSchema])
async def list_employee_adaptations(db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await get_employee_adaptations(db)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/employee-adaptations/{adaptation_id}/", response_model=EmployeeAdaptationSchema)
async def read_employee_adaptation(adaptation_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await get_employee_adaptation(db, adaptation_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/assign/", response_model=EmployeeAdaptationSchema)
async def assign_adaptation_route(data: EmployeeAdaptationCreate, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await assign_adaptation(db, data)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/employee-adaptations/{adaptation_id}/", response_model=dict)
async def delete_employee_adaptation_route(adaptation_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        ok = await delete_employee_adaptation(db, adaptation_id)
        return {"success": bool(ok)}
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


# Element status
@router.put("/elements/{element_id}/status/", response_model=dict)
async def update_element_status_route(element_id: int, body: UpdateElementStatusRequest, employee_adaptation_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await update_element_status(db, element_id, employee_adaptation_id, body.is_completed, user.id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


# Stats and progress
@router.get("/stats/", response_model=dict)
async def stats_route(db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    return await get_stats(db)


@router.get("/progress/{adaptation_id}/", response_model=list[dict])
async def progress_route(adaptation_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    return await get_progress(db, adaptation_id)


@router.post("/copy/", response_model=EmployeeAdaptationSchema)
async def copy_adaptation_route(body: CopyAdaptationRequest, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await copy_adaptation(db, body.source_adaptation_id, body.target_employee_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


# Sections
@router.post("/templates/{template_id}/sections/", response_model=AdaptationSectionSchema)
async def create_section_route(template_id: int, data: AdaptationSectionCreate, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        if data.template_id != template_id:
            raise HTTPException(status_code=400, detail="template_id mismatch")
        return await create_section(db, data)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sections/{section_id}/", response_model=AdaptationSectionSchema)
async def update_section_route(section_id: int, data: AdaptationSectionUpdate, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await update_section(db, section_id, data)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sections/{section_id}/", response_model=dict)
async def delete_section_route(section_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        ok = await delete_section(db, section_id)
        return {"success": bool(ok)}
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


# Elements
@router.post("/sections/{section_id}/elements/", response_model=AdaptationElementSchema)
async def create_element_route(section_id: int, data: AdaptationElementCreate, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        if data.section_id != section_id:
            raise HTTPException(status_code=400, detail="section_id mismatch")
        return await create_element(db, data)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/elements/{element_id}/", response_model=AdaptationElementSchema)
async def update_element_route(element_id: int, data: AdaptationElementUpdate, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await update_element(db, element_id, data)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/elements/{element_id}/", response_model=dict)
async def delete_element_route(element_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        ok = await delete_element(db, element_id)
        return {"success": bool(ok)}
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


# User adaptations
@router.get("/users/{user_id}/adaptations/", response_model=list[UserAdaptationProgress])
async def get_user_adaptations_route(user_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await get_user_adaptations(db, user_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{user_id}/adaptations/{adaptation_id}/", response_model=EmployeeAdaptationSchema)
async def update_user_adaptation_route(
    user_id: int, 
    adaptation_id: int, 
    data: UpdateAdaptationRequest, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(authorized_required)
):
    try:
        update_data = data.model_dump(exclude_unset=True)
        return await update_user_adaptation(db, user_id, adaptation_id, update_data)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


