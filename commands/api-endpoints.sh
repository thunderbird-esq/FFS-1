#!/bin/bash
# Generate complete FastAPI endpoint structure with all CRUD operations

# Parse arguments
RESOURCE="${1:-items}"
METHODS="${2:-GET POST PUT DELETE}"
OUTPUT_DIR="${3:-app/api/endpoints}"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Generate the complete endpoint file
python3 << EOF
import sys
import os
from pathlib import Path

resource = "$RESOURCE"
methods = "$METHODS".split()
output_dir = Path("$OUTPUT_DIR")
output_dir.mkdir(parents=True, exist_ok=True)

# Generate schema file
schema_content = f'''from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class {resource.capitalize()}Base(BaseModel):
    """Base schema for {resource}."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: bool = Field(True)

class {resource.capitalize()}Create({resource.capitalize()}Base):
    """Schema for creating {resource}."""
    pass

class {resource.capitalize()}Update(BaseModel):
    """Schema for updating {resource}."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None

class {resource.capitalize()}Response({resource.capitalize()}Base):
    """Schema for {resource} responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
'''

# Generate repository file
repository_content = f'''from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.{resource} import {resource.capitalize()}

class {resource.capitalize()}Repository:
    """Repository for {resource} operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, data: dict) -> {resource.capitalize()}:
        """Create new {resource}."""
        db_obj = {resource.capitalize()}(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def get(self, id: int) -> Optional[{resource.capitalize()}]:
        """Get {resource} by ID."""
        result = await self.db.execute(
            select({resource.capitalize()}).where({resource.capitalize()}.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[{resource.capitalize()}]:
        """Get multiple {resource}s."""
        result = await self.db.execute(
            select({resource.capitalize()}).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def update(self, id: int, data: dict) -> Optional[{resource.capitalize()}]:
        """Update {resource}."""
        await self.db.execute(
            update({resource.capitalize()}).where({resource.capitalize()}.id == id).values(**data)
        )
        await self.db.commit()
        return await self.get(id)
    
    async def delete(self, id: int) -> bool:
        """Delete {resource}."""
        result = await self.db.execute(
            delete({resource.capitalize()}).where({resource.capitalize()}.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
'''

# Generate endpoint file
endpoint_content = f'''from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.{resource} import (
    {resource.capitalize()}Create,
    {resource.capitalize()}Update,
    {resource.capitalize()}Response
)
from app.repositories.{resource} import {resource.capitalize()}Repository
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()

'''

if "GET" in methods:
    endpoint_content += f'''@router.get("/", response_model=List[{resource.capitalize()}Response])
async def get_{resource}s(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all {resource}s with pagination."""
    repo = {resource.capitalize()}Repository(db)
    return await repo.get_multi(skip=skip, limit=limit)

@router.get("/{{{resource}_id}}", response_model={resource.capitalize()}Response)
async def get_{resource}(
    {resource}_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific {resource} by ID."""
    repo = {resource.capitalize()}Repository(db)
    obj = await repo.get({resource}_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource.capitalize()} not found"
        )
    return obj

'''

if "POST" in methods:
    endpoint_content += f'''@router.post("/", response_model={resource.capitalize()}Response, status_code=status.HTTP_201_CREATED)
async def create_{resource}(
    data: {resource.capitalize()}Create,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new {resource}."""
    repo = {resource.capitalize()}Repository(db)
    return await repo.create(data.dict())

'''

if "PUT" in methods:
    endpoint_content += f'''@router.put("/{{{resource}_id}}", response_model={resource.capitalize()}Response)
async def update_{resource}(
    {resource}_id: int,
    data: {resource.capitalize()}Update,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update existing {resource}."""
    repo = {resource.capitalize()}Repository(db)
    obj = await repo.get({resource}_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource.capitalize()} not found"
        )
    return await repo.update({resource}_id, data.dict(exclude_unset=True))

'''

if "DELETE" in methods:
    endpoint_content += f'''@router.delete("/{{{resource}_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{resource}(
    {resource}_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete {resource}."""
    repo = {resource.capitalize()}Repository(db)
    obj = await repo.get({resource}_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource.capitalize()} not found"
        )
    await repo.delete({resource}_id)
'''

# Write files
with open(output_dir / f"{resource}.py", "w") as f:
    f.write(endpoint_content)

with open(output_dir.parent / "schemas" / f"{resource}.py", "w") as f:
    f.write(schema_content)

with open(output_dir.parent / "repositories" / f"{resource}.py", "w") as f:
    f.write(repository_content)

print(f"✓ Generated FastAPI endpoints for '{resource}':")
print(f"  - {output_dir}/{resource}.py")
print(f"  - schemas/{resource}.py")
print(f"  - repositories/{resource}.py")
print(f"  Methods: {', '.join(methods)}")
EOF

# Handle any additional arguments passed via $ARGUMENTS
if [ -n "$ARGUMENTS" ]; then
    echo "Processing additional arguments: $ARGUMENTS"
    # Additional processing based on arguments
    python3 -c "
args = '$ARGUMENTS'.split()
for arg in args:
    if arg.startswith('--'):
        print(f'  Option: {arg}')
"
fi
