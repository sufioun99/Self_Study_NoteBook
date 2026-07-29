from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
from ..models import (
    create_material, get_material, list_materials, update_material, delete_material,
    create_version, get_version, list_versions, get_version_chain,
    create_block, list_blocks,
    create_tag, list_tags, tag_material, untag_material, get_material_tags,
    create_relation, get_relations, get_recent_materials, get_related_materials,
)

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("/recent")
def recent_materials_endpoint(limit: int = Query(default=10)):
    return get_recent_materials(limit=limit)


@router.post("/")
def create_material_endpoint(
    title: str = Body(...),
    material_type: str = Body("note"),
    topic_summary: Optional[str] = Body(None),
):
    material = create_material(title, material_type, topic_summary)
    return material


@router.get("/")
def list_materials_endpoint(limit: int = Query(50), offset: int = Query(0)):
    return list_materials(limit=limit, offset=offset)


@router.get("/{material_id}")
def get_material_endpoint(material_id: int):
    material = get_material(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    material["tags"] = get_material_tags(material_id)
    material["relations"] = get_relations(material_id)
    material["versions"] = get_version_chain(material_id)
    return material


@router.put("/{material_id}")
def update_material_endpoint(
    material_id: int,
    title: Optional[str] = Body(None),
    material_type: Optional[str] = Body(None),
    topic_summary: Optional[str] = Body(None),
    status: Optional[str] = Body(None),
):
    material = get_material(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return update_material(material_id, title=title, material_type=material_type,
                           topic_summary=topic_summary, status=status)


@router.delete("/{material_id}")
def delete_material_endpoint(material_id: int):
    material = get_material(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    delete_material(material_id)
    return {"deleted": material_id}


@router.post("/{material_id}/versions")
def create_version_endpoint(
    material_id: int,
    language: Optional[str] = Body(None),
    change_note: Optional[str] = Body(None),
    test_status: str = Body("untested"),
):
    material = get_material(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    versions = list_versions(material_id)
    next_version = len(versions) + 1
    parent_id = versions[-1]["id"] if versions else None
    version = create_version(material_id, parent_version_id=parent_id,
                             version_number=next_version, language=language,
                             change_note=change_note, test_status=test_status)
    return version


@router.get("/{material_id}/versions")
def list_versions_endpoint(material_id: int):
    return list_versions(material_id)


@router.get("/{material_id}/versions/{version_id}/chain")
def version_chain_endpoint(material_id: int, version_id: int):
    chain = get_version_chain(material_id)
    return chain


@router.post("/{material_id}/versions/{version_id}/blocks")
def create_block_endpoint(
    material_id: int,
    version_id: int,
    block_order: int = Body(0),
    block_type: str = Body("text"),
    language: Optional[str] = Body(None),
    text_content: Optional[str] = Body(None),
    code_content: Optional[str] = Body(None),
    alt_text: Optional[str] = Body(None),
    source_ref: Optional[str] = Body(None),
):
    block = create_block(version_id, block_order, block_type, language,
                         text_content, code_content, alt_text, source_ref)
    return block


@router.get("/{material_id}/versions/{version_id}/blocks")
def list_blocks_endpoint(material_id: int, version_id: int):
    return list_blocks(version_id)


@router.post("/{material_id}/tags")
def tag_material_endpoint(
    material_id: int,
    tag_name: str = Body(..., embed=True),
):
    tag = create_tag(tag_name)
    if tag:
        tag_material(material_id, tag["id"])
    return {"material_id": material_id, "tag": tag}


@router.delete("/{material_id}/tags/{tag_id}")
def untag_material_endpoint(material_id: int, tag_id: int):
    untag_material(material_id, tag_id)
    return {"material_id": material_id, "tag_id": tag_id}


@router.get("/{material_id}/tags")
def get_material_tags_endpoint(material_id: int):
    return get_material_tags(material_id)


@router.post("/{material_id}/relations")
def create_relation_endpoint(
    material_id: int,
    to_material_id: int = Body(...),
    relation_type: str = Body("related"),
    note: Optional[str] = Body(None),
    strength: float = Body(1.0),
):
    create_relation(material_id, to_material_id, relation_type, note, strength)
    return {"from": material_id, "to": to_material_id, "type": relation_type}


@router.get("/{material_id}/relations")
def get_relations_endpoint(material_id: int):
    return get_relations(material_id)


@router.get("/{material_id}/related")
def related_materials_endpoint(material_id: int, limit: int = Query(5)):
    return get_related_materials(material_id, limit=limit)
