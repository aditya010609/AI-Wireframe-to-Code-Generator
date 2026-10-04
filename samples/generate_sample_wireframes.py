import os
from PIL import Image, ImageDraw, ImageFont


def create_wireframe_image(title: str, components: list, width: int = 800, height: int = 600) -> Image.Image:
    """Create a sleek blueprint/wireframe style PNG image for benchmarking and testing."""
    # Dark blueprint background
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Draw grid lines for wireframe blueprint aesthetic
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=(30, 41, 59), width=1)
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=(30, 41, 59), width=1)

    # Draw wireframe elements
    for comp in components:
        comp_type = comp.get("type")
        bbox = comp.get("bbox") # [x1, y1, x2, y2]
        label = comp.get("label", "")
        
        x1, y1, x2, y2 = bbox

        if comp_type == "header":
            draw.rectangle([x1, y1, x2, y2], outline=(99, 102, 241), width=2, fill=(30, 41, 59))
            draw.text((x1 + 15, y1 + 12), f"[HEADER] {label}", fill=(248, 250, 252))
            
        elif comp_type == "hero":
            draw.rectangle([x1, y1, x2, y2], outline=(129, 140, 248), width=2, fill=(30, 41, 59))
            draw.text((x1 + 20, y1 + 20), f"[HERO SECTION] {label}", fill=(248, 250, 252))
            
        elif comp_type == "button":
            draw.rectangle([x1, y1, x2, y2], outline=(99, 102, 241), width=2, fill=(79, 70, 229))
            draw.text((x1 + 15, y1 + 10), label, fill=(255, 255, 255))
            
        elif comp_type == "card":
            draw.rectangle([x1, y1, x2, y2], outline=(148, 163, 184), width=2, fill=(30, 41, 59))
            draw.text((x1 + 15, y1 + 15), f"[CARD] {label}", fill=(226, 232, 240))
            
        elif comp_type == "input":
            draw.rectangle([x1, y1, x2, y2], outline=(71, 85, 105), width=2, fill=(15, 23, 42))
            draw.text((x1 + 10, y1 + 10), f"Input: {label}", fill=(148, 163, 184))
            
        elif comp_type == "sidebar":
            draw.rectangle([x1, y1, x2, y2], outline=(99, 102, 241), width=2, fill=(30, 41, 59))
            draw.text((x1 + 15, y1 + 20), f"[SIDEBAR] {label}", fill=(226, 232, 240))
            
        elif comp_type == "table":
            draw.rectangle([x1, y1, x2, y2], outline=(148, 163, 184), width=2, fill=(30, 41, 59))
            draw.text((x1 + 15, y1 + 15), f"[DATA TABLE] {label}", fill=(226, 232, 240))
            
        elif comp_type == "footer":
            draw.rectangle([x1, y1, x2, y2], outline=(71, 85, 105), width=2, fill=(30, 41, 59))
            draw.text((x1 + 15, y1 + 15), f"[FOOTER] {label}", fill=(148, 163, 184))

    return img


def generate_all_samples(output_dir: str = "samples"):
    os.makedirs(output_dir, exist_ok=True)

    # 1. Landing Page Wireframe
    landing_comps = [
        {"type": "header", "bbox": [20, 20, 780, 70], "label": "Logo | Nav Links: Features, Pricing, About | Login CTA"},
        {"type": "hero", "bbox": [20, 90, 780, 280], "label": "Build GenAI Apps Faster - Headline & Subtitle"},
        {"type": "button", "bbox": [50, 220, 200, 260], "label": "Get Started Free"},
        {"type": "button", "bbox": [220, 220, 350, 260], "label": "Watch Demo"},
        {"type": "card", "bbox": [20, 300, 260, 480], "label": "Feature 1: AI Vision Extraction"},
        {"type": "card", "bbox": [280, 300, 520, 480], "label": "Feature 2: Pydantic Validation"},
        {"type": "card", "bbox": [540, 300, 780, 480], "label": "Feature 3: Responsive Tailwind Code"},
        {"type": "footer", "bbox": [20, 500, 780, 570], "label": "© 2026 AI Wireframe Engine. All rights reserved."}
    ]
    img_landing = create_wireframe_image("Landing Page", landing_comps)
    img_landing.save(os.path.join(output_dir, "landing_page_wireframe.png"))

    # 2. Analytics Dashboard Wireframe
    dash_comps = [
        {"type": "sidebar", "bbox": [20, 20, 200, 580], "label": "Navigation: Home, Analytics, Users, Settings"},
        {"type": "header", "bbox": [220, 20, 780, 80], "label": "Search Bar & User Avatar Profile"},
        {"type": "card", "bbox": [220, 100, 390, 200], "label": "Total Revenue: $48,250 (+12%)"},
        {"type": "card", "bbox": [410, 100, 580, 200], "label": "Active Users: 3,420 (+8%)"},
        {"type": "card", "bbox": [600, 100, 780, 200], "label": "Conversion Rate: 4.8%"},
        {"type": "table", "bbox": [220, 220, 780, 580], "label": "Recent User Signups & Transaction Log"}
    ]
    img_dash = create_wireframe_image("Analytics Dashboard", dash_comps)
    img_dash.save(os.path.join(output_dir, "dashboard_wireframe.png"))

    # 3. User Login Modal Wireframe
    login_comps = [
        {"type": "card", "bbox": [200, 60, 600, 520], "label": "Sign In to Your Account"},
        {"type": "input", "bbox": [240, 160, 560, 210], "label": "Email Address (name@example.com)"},
        {"type": "input", "bbox": [240, 240, 560, 290], "label": "Password"},
        {"type": "button", "bbox": [240, 320, 560, 370], "label": "Sign In"},
        {"type": "button", "bbox": [240, 390, 560, 440], "label": "Continue with Google"}
    ]
    img_login = create_wireframe_image("Login Screen", login_comps)
    img_login.save(os.path.join(output_dir, "login_wireframe.png"))

    print("Sample wireframes generated successfully in", output_dir)


if __name__ == "__main__":
    generate_all_samples()
