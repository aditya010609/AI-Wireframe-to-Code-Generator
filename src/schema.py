from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    # Structural / Layout Containers
    HEADER = "header"
    NAVBAR = "navbar"
    HERO = "hero"
    SECTION = "section"
    GRID = "grid"
    FLEX = "flex"
    CARD = "card"
    SIDEBAR = "sidebar"
    FOOTER = "footer"
    MODAL = "modal"
    FORM = "form"
    CONTAINER = "container"
    
    # Text & Typography
    HEADING = "heading"
    TEXT = "text"
    BADGE = "badge"
    STAT = "stat"
    
    # Interactive Inputs & Controls
    BUTTON = "button"
    INPUT = "input"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    
    # Media & Display
    IMAGE = "image"
    ICON = "icon"
    AVATAR = "avatar"
    TABLE = "table"
    LIST = "list"
    NAV_ITEM = "nav_item"


class StyleConfig(BaseModel):
    """Tailwind styling tokens and properties for a UI AST Node."""
    bg_color: str = Field(default="", description="Tailwind background color (e.g. bg-slate-900, bg-indigo-600)")
    text_color: str = Field(default="", description="Tailwind text color (e.g. text-white, text-slate-300)")
    font_size: str = Field(default="", description="Tailwind font size (e.g. text-sm, text-xl, text-4xl)")
    font_weight: str = Field(default="", description="Tailwind font weight (e.g. font-medium, font-bold)")
    text_align: str = Field(default="", description="Tailwind text alignment (e.g. text-center, text-left)")
    padding: str = Field(default="", description="Tailwind padding (e.g. p-4, px-6 py-3)")
    margin: str = Field(default="", description="Tailwind margin (e.g. mb-4, mx-auto)")
    border: str = Field(default="", description="Tailwind border/rounded/shadow (e.g. border border-slate-700 rounded-xl shadow-md)")
    width: str = Field(default="", description="Tailwind width (e.g. w-full, w-1/2, max-w-md)")
    height: str = Field(default="", description="Tailwind height (e.g. h-auto, h-12, h-full)")
    flex_direction: str = Field(default="", description="Flex direction if layout (e.g. flex-row, flex-col)")
    justify_content: str = Field(default="", description="Flex justification (e.g. justify-between, justify-center)")
    align_items: str = Field(default="", description="Flex item alignment (e.g. items-center, items-start)")
    gap: str = Field(default="", description="Gap spacing (e.g. gap-4, gap-6)")
    grid_cols: str = Field(default="", description="Grid template columns (e.g. grid-cols-1 md:grid-cols-3)")
    custom_classes: str = Field(default="", description="Additional Tailwind utility classes")


class UIASTNode(BaseModel):
    """Hierarchical UI element node representing layout, text, or widget."""
    id: str = Field(..., description="Unique node identifier, e.g. node-1, hero-title, submit-btn")
    type: ComponentType = Field(..., description="Type of component from ComponentType enum")
    label: Optional[str] = Field(default=None, description="Display text, title, or button label")
    placeholder: Optional[str] = Field(default=None, description="Input placeholder text")
    src: Optional[str] = Field(default=None, description="Image source or icon reference")
    href: Optional[str] = Field(default=None, description="Link target URL")
    variant: Optional[str] = Field(default=None, description="Component variant e.g. primary, secondary, outline, danger")
    icon_name: Optional[str] = Field(default=None, description="Lucide icon identifier e.g. search, user, check, zap")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional custom component attributes")
    style: StyleConfig = Field(default_factory=StyleConfig, description="Tailwind styling rules")
    children: List['UIASTNode'] = Field(default_factory=list, description="Child nodes nested inside this container")


class UIPageAST(BaseModel):
    """Top-level Root Page document containing full component hierarchy."""
    title: str = Field(default="Generated UI Page", description="Page title")
    description: Optional[str] = Field(default=None, description="Brief description of the wireframe composition")
    theme: str = Field(default="dark", description="Overall theme variant: dark or light")
    root: UIASTNode = Field(..., description="Root container node")
    version: int = Field(default=1, description="AST version number")


# Enable self-referencing forward references in Pydantic v2
UIASTNode.model_rebuild()
