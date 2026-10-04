import html
from typing import List
from src.schema import UIPageAST, UIASTNode, ComponentType, StyleConfig


def compile_style_classes(style: StyleConfig) -> str:
    """Combine StyleConfig attributes into a single clean Tailwind class string."""
    classes = []
    
    if style.bg_color: classes.append(style.bg_color)
    if style.text_color: classes.append(style.text_color)
    if style.font_size: classes.append(style.font_size)
    if style.font_weight: classes.append(style.font_weight)
    if style.text_align: classes.append(style.text_align)
    if style.padding: classes.append(style.padding)
    if style.margin: classes.append(style.margin)
    if style.border: classes.append(style.border)
    if style.width: classes.append(style.width)
    if style.height: classes.append(style.height)
    if style.flex_direction: classes.append(style.flex_direction)
    if style.justify_content: classes.append(style.justify_content)
    if style.align_items: classes.append(style.align_items)
    if style.gap: classes.append(style.gap)
    if style.grid_cols: classes.append(style.grid_cols)
    if style.custom_classes: classes.append(style.custom_classes)
    
    return " ".join(classes).strip()


def sanitize_text(text: str) -> str:
    """Sanitize user text input to prevent XSS injection."""
    if not text:
        return ""
    return html.escape(str(text))


def render_node(node: UIASTNode) -> str:
    """Recursively render a UIASTNode into clean responsive Tailwind HTML5 markup."""
    style_str = compile_style_classes(node.style)
    class_attr = f'class="{style_str}"' if style_str else ""
    node_id = f'id="{sanitize_text(node.id)}"'
    
    label = sanitize_text(node.label or "")
    placeholder = sanitize_text(node.placeholder or "")
    href = sanitize_text(node.href or "#")
    src = sanitize_text(node.src or "")
    icon_name = sanitize_text(node.icon_name or "")
    
    # Render children nodes recursively
    children_html = "".join(render_node(child) for child in node.children)
    
    icon_tag = f'<i data-lucide="{icon_name}" class="w-5 h-5 inline-block mr-2"></i>' if icon_name else ""

    # Map ComponentType to standard HTML5 elements
    ct = node.type

    if ct == ComponentType.HEADER:
        return f'<header {node_id} {class_attr}>{children_html}</header>'
        
    elif ct == ComponentType.NAVBAR:
        return f'<nav {node_id} {class_attr}>{children_html}</nav>'
        
    elif ct == ComponentType.HERO or ct == ComponentType.SECTION:
        return f'<section {node_id} {class_attr}>{children_html}</section>'
        
    elif ct == ComponentType.GRID:
        default_grid = "grid grid-cols-1 md:grid-cols-3 gap-6" if "grid" not in style_str else "grid"
        return f'<div {node_id} class="{default_grid} {style_str}">{children_html}</div>'
        
    elif ct == ComponentType.FLEX or ct == ComponentType.CONTAINER:
        default_flex = "flex flex-col" if ("flex" not in style_str and "block" not in style_str) else ""
        return f'<div {node_id} class="{default_flex} {style_str}">{children_html}</div>'
        
    elif ct == ComponentType.CARD:
        default_card = "bg-slate-800/80 border border-slate-700/60 rounded-xl p-6 shadow-xl" if not style_str else style_str
        return f'<div {node_id} class="{default_card}">{children_html}</div>'
        
    elif ct == ComponentType.SIDEBAR:
        return f'<aside {node_id} {class_attr}>{children_html}</aside>'
        
    elif ct == ComponentType.FOOTER:
        return f'<footer {node_id} {class_attr}>{children_html}</footer>'
        
    elif ct == ComponentType.FORM:
        return f'<form {node_id} {class_attr} onsubmit="event.preventDefault();">{children_html}</form>'
        
    elif ct == ComponentType.HEADING:
        # Choose tag based on font size or variant
        tag = "h2"
        if "text-4xl" in style_str or "text-3xl" in style_str:
            tag = "h1"
        elif "text-xl" in style_str:
            tag = "h3"
        elif "text-lg" in style_str:
            tag = "h4"
        return f'<{tag} {node_id} {class_attr}>{icon_tag}{label}{children_html}</{tag}>'
        
    elif ct == ComponentType.TEXT:
        return f'<p {node_id} {class_attr}>{icon_tag}{label}{children_html}</p>'
        
    elif ct == ComponentType.BADGE:
        default_badge = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30"
        final_class = style_str if style_str else default_badge
        return f'<span {node_id} class="{final_class}">{icon_tag}{label}</span>'
        
    elif ct == ComponentType.STAT:
        subtext = node.attributes.get("subtext", "")
        return f'''<div {node_id} class="p-4 bg-slate-800/60 border border-slate-700 rounded-lg {style_str}">
            <div class="text-xs font-medium text-slate-400">{label}</div>
            <div class="text-2xl font-bold text-white mt-1">{children_html or sanitize_text(node.attributes.get("value", "0"))}</div>
            {f'<div class="text-xs text-emerald-400 mt-1">{sanitize_text(subtext)}</div>' if subtext else ''}
        </div>'''
        
    elif ct == ComponentType.BUTTON:
        btn_variant = node.variant or "primary"
        variant_class = "bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-5 py-2.5 rounded-lg shadow-md transition-all duration-200 cursor-pointer"
        if btn_variant == "secondary":
            variant_class = "bg-slate-700 hover:bg-slate-600 text-white font-medium px-5 py-2.5 rounded-lg transition-all cursor-pointer"
        elif btn_variant == "outline":
            variant_class = "border border-slate-600 hover:bg-slate-800 text-slate-200 font-medium px-5 py-2.5 rounded-lg transition-all cursor-pointer"
        elif btn_variant == "danger":
            variant_class = "bg-rose-600 hover:bg-rose-500 text-white font-medium px-5 py-2.5 rounded-lg transition-all cursor-pointer"

        final_class = style_str if style_str else variant_class
        return f'<button {node_id} class="{final_class}">{icon_tag}{label}{children_html}</button>'
        
    elif ct == ComponentType.INPUT:
        inputType = node.attributes.get("input_type", "text")
        default_input = "w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        final_class = style_str if style_str else default_input
        return f'<input {node_id} type="{inputType}" placeholder="{placeholder}" value="{label}" class="{final_class}" />'
        
    elif ct == ComponentType.TEXTAREA:
        default_area = "w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        final_class = style_str if style_str else default_area
        return f'<textarea {node_id} placeholder="{placeholder}" class="{final_class}">{label}</textarea>'
        
    elif ct == ComponentType.SELECT:
        options = node.attributes.get("options", ["Option 1", "Option 2", "Option 3"])
        opt_html = "".join(f'<option value="{sanitize_text(opt)}">{sanitize_text(opt)}</option>' for opt in options)
        default_select = "w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
        final_class = style_str if style_str else default_select
        return f'<select {node_id} class="{final_class}">{opt_html}</select>'
        
    elif ct == ComponentType.CHECKBOX:
        return f'''<label class="inline-flex items-center gap-2 cursor-pointer">
            <input {node_id} type="checkbox" class="w-4 h-4 text-indigo-600 bg-slate-900 border-slate-700 rounded focus:ring-indigo-500" />
            <span class="text-sm text-slate-300">{label}</span>
        </label>'''
        
    elif ct == ComponentType.IMAGE:
        img_src = src or "https://placehold.co/600x400/1e293b/94a3b8?text=Image+Placeholder"
        default_img = "w-full h-auto rounded-lg object-cover"
        final_class = style_str if style_str else default_img
        return f'<img {node_id} src="{img_src}" alt="{label or "UI Image"}" class="{final_class}" />'
        
    elif ct == ComponentType.ICON:
        icon_name_val = icon_name or label or "sparkles"
        return f'<i {node_id} data-lucide="{icon_name_val}" class="w-6 h-6 {style_str}"></i>'
        
    elif ct == ComponentType.AVATAR:
        avatar_src = src or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80"
        return f'<img {node_id} src="{avatar_src}" alt="{label or "User"}" class="w-10 h-10 rounded-full object-cover border-2 border-indigo-500/50 {style_str}" />'
        
    elif ct == ComponentType.NAV_ITEM:
        return f'<a {node_id} href="{href}" class="text-slate-300 hover:text-white transition-colors duration-200 font-medium text-sm px-3 py-2 rounded-md hover:bg-slate-800 {style_str}">{icon_tag}{label}</a>'
        
    elif ct == ComponentType.TABLE:
        headers = node.attributes.get("headers", ["Name", "Status", "Role", "Action"])
        rows = node.attributes.get("rows", [
            ["Alice Johnson", "Active", "Admin", "Edit"],
            ["Bob Smith", "Pending", "User", "View"],
            ["Carol White", "Active", "Editor", "Edit"]
        ])
        
        th_html = "".join(f'<th class="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">{sanitize_text(h)}</th>' for h in headers)
        
        tr_html = ""
        for row in rows:
            td_html = "".join(f'<td class="px-6 py-4 whitespace-nowrap text-sm text-slate-300">{sanitize_text(c)}</td>' for c in row)
            tr_html += f'<tr class="hover:bg-slate-800/40 border-b border-slate-800">{td_html}</tr>'
            
        return f'''<div {node_id} class="overflow-x-auto rounded-lg border border-slate-700 bg-slate-900/60 {style_str}">
            <table class="min-w-full divide-y divide-slate-800">
                <thead class="bg-slate-800/80">
                    <tr>{th_html}</tr>
                </thead>
                <tbody class="divide-y divide-slate-800">{tr_html}</tbody>
            </table>
        </div>'''
        
    elif ct == ComponentType.LIST:
        items = node.attributes.get("items", ["Item 1", "Item 2", "Item 3"])
        li_html = "".join(f'<li class="py-1 text-slate-300 flex items-center gap-2"><i data-lucide="check-circle" class="w-4 h-4 text-indigo-400"></i>{sanitize_text(it)}</li>' for it in items)
        return f'<ul {node_id} class="space-y-2 {style_str}">{li_html}{children_html}</ul>'
        
    else:
        # Default fallback container
        return f'<div {node_id} {class_attr}>{children_html or label}</div>'


def generate_html_document(ast: UIPageAST) -> str:
    """Convert top-level UIPageAST into a full standalone responsive Tailwind HTML5 webpage."""
    root_body_html = render_node(ast.root)
    
    bg_theme = "bg-slate-950 text-slate-100" if ast.theme == "dark" else "bg-slate-50 text-slate-900"
    
    html_doc = f"""<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{sanitize_text(ast.title)}</title>
    <!-- Google Fonts: Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['Inter', 'sans-serif'],
                    }},
                }}
            }}
        }}
    </script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            -webkit-font-smoothing: antialiased;
        }}
    </style>
</head>
<body class="min-h-full {bg_theme} antialiased selection:bg-indigo-500 selection:text-white">
    {root_body_html}
    <script>
        // Initialize Lucide Icons on load
        document.addEventListener('DOMContentLoaded', () => {{
            if (typeof lucide !== 'undefined') {{
                lucide.createIcons();
            }}
        }});
        // Fallback icon creation if DOMContentLoaded already fired
        if (typeof lucide !== 'undefined') {{
            lucide.createIcons();
        }}
    </script>
</body>
</html>
"""
    return html_doc
