#!/usr/bin/env python3
"""
Restaurant Icon Downloader
Download and organize restaurant technology icons from various sources
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from bs4 import BeautifulSoup
import time

log = logging.getLogger(__name__)

@dataclass
class RestaurantIcon:
    name: str
    device_type: str
    pos_system: Optional[str]
    svg_path: Optional[str] = None
    png_path: Optional[str] = None
    source_url: Optional[str] = None

class RestaurantIconDownloader:
    """Download restaurant technology icons from various sources"""
    
    def __init__(self, output_dir: str = "restaurant_icons"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.svg_dir = self.output_dir / "svg"
        self.svg_dir.mkdir(exist_ok=True)
        self.png_dir = self.output_dir / "png"
        self.png_dir.mkdir(exist_ok=True)
        self.metadata_file = self.output_dir / "icon_mapping.json"
        
        # Restaurant device types to download
        self.device_types = {
            'pos_register': ['POS Register', 'Cash Register', 'POS Terminal', 'Checkout'],
            'pos_tablet': ['POS Tablet', 'iPad POS', 'Tablet Ordering', 'Mobile POS'],
            'kitchen_display': ['Kitchen Display', 'KDS', 'Kitchen Monitor', 'Display'],
            'digital_menu': ['Digital Menu', 'Menu Board', 'Digital Display', 'Menu Display'],
            'kitchen_printer': ['Kitchen Printer', 'Receipt Printer', 'Thermal Printer'],
            'payment_terminal': ['Payment Terminal', 'Credit Card Terminal', 'Payment Device']
        }
        
        # POS system specific searches
        self.pos_systems = {
            'Clover': ['Clover POS', 'Clover Station', 'Clover Mini', 'Clover Flex'],
            'Square': ['Square Terminal', 'Square Stand', 'Square Reader'],
            'Toast': ['Toast POS', 'Toast Terminal'],
            'NCR': ['NCR Aloha', 'NCR POS'],
            'Micros': ['Micros POS', 'Micros Terminal']
        }
    
    def download_icons8_icons(self) -> List[RestaurantIcon]:
        """Download icons from Icons8 (requires API key or web scraping)"""
        icons = []
        
        try:
            # Icons8 API would require authentication
            # For now, we'll create placeholder entries
            log.info("Icons8 requires API key - creating placeholder entries")
            
            for device_type, search_terms in self.device_types.items():
                for term in search_terms:
                    icon = RestaurantIcon(
                        name=f"{term} Icon",
                        device_type=device_type,
                        pos_system=None,
                        source_url="https://icons8.com/icons/set/pos"
                    )
                    icons.append(icon)
            
        except Exception as e:
            log.error(f"Failed to download from Icons8: {e}")
        
        return icons
    
    def download_freepik_icons(self) -> List[RestaurantIcon]:
        """Download free icons from Freepik"""
        icons = []
        
        try:
            # Freepik free icons search
            base_url = "https://www.freepik.com/search"
            
            for device_type, search_terms in self.device_types.items():
                for term in search_terms:
                    search_url = f"{base_url}?format=search&query={term.replace(' ', '+')}+icon"
                    
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        response = requests.get(search_url, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Look for free icon links (simplified - actual implementation would need more specific selectors)
                            icon_links = soup.find_all('a', class_='show-content')
                            
                            for link in icon_links[:3]:  # Limit to first 3 results
                                icon_url = link.get('href')
                                if icon_url:
                                    icon = RestaurantIcon(
                                        name=f"{term} - Freepik",
                                        device_type=device_type,
                                        pos_system=None,
                                        source_url=icon_url
                                    )
                                    icons.append(icon)
                        
                        time.sleep(1)  # Be respectful to the server
                        
                    except Exception as e:
                        log.warning(f"Failed to search Freepik for {term}: {e}")
            
        except Exception as e:
            log.error(f"Failed to download from Freepik: {e}")
        
        return icons
    
    def create_placeholder_icons(self) -> List[RestaurantIcon]:
        """Create placeholder SVG icons for restaurant devices"""
        icons = []
        
        # Basic SVG templates for different restaurant devices
        svg_templates = {
            'pos_register': '''<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
                <rect width="64" height="64" fill="#2E7D32" rx="4"/>
                <rect x="8" y="16" width="48" height="32" fill="#1B5E20" rx="2"/>
                <rect x="12" y="20" width="40" height="24" fill="#4CAF50"/>
                <text x="32" y="35" text-anchor="middle" fill="white" font-family="Arial" font-size="10">POS</text>
                <circle cx="32" cy="52" r="2" fill="#81C784"/>
            </svg>''',
            
            'pos_tablet': '''<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
                <rect width="64" height="64" fill="#1976D2" rx="8"/>
                <rect x="6" y="8" width="52" height="48" fill="#0D47A1" rx="4"/>
                <rect x="10" y="12" width="44" height="36" fill="#2196F3"/>
                <circle cx="32" cy="54" r="2" fill="#64B5F6"/>
            </svg>''',
            
            'kitchen_display': '''<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
                <rect width="64" height="64" fill="#FF6F00" rx="2"/>
                <rect x="4" y="8" width="56" height="40" fill="#E65100" rx="2"/>
                <rect x="8" y="12" width="48" height="32" fill="#FFB74D"/>
                <line x1="12" y1="20" x2="52" y2="20" stroke="#E65100" stroke-width="2"/>
                <line x1="12" y1="28" x2="52" y2="28" stroke="#E65100" stroke-width="2"/>
                <line x1="12" y1="36" x2="52" y2="36" stroke="#E65100" stroke-width="2"/>
            </svg>''',
            
            'digital_menu': '''<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
                <rect width="64" height="64" fill="#7B1FA2" rx="2"/>
                <rect x="4" y="4" width="56" height="56" fill="#4A148C" rx="2"/>
                <rect x="8" y="8" width="48" height="48" fill="#9C27B0"/>
                <text x="32" y="25" text-anchor="middle" fill="white" font-family="Arial" font-size="8">MENU</text>
                <text x="32" y="35" text-anchor="middle" fill="white" font-family="Arial" font-size="6">$12.99</text>
                <text x="32" y="45" text-anchor="middle" fill="white" font-family="Arial" font-size="6">$8.99</text>
            </svg>''',
            
            'kitchen_printer': '''<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
                <rect width="64" height="64" fill="#5D4037" rx="2"/>
                <rect x="8" y="16" width="48" height="32" fill="#3E2723" rx="2"/>
                <rect x="12" y="20" width="40" height="24" fill="#8D6E63"/>
                <rect x="16" y="24" width="32" height="2" fill="white"/>
                <rect x="16" y="28" width="32" height="2" fill="white"/>
                <rect x="16" y="32" width="32" height="2" fill="white"/>
                <rect x="16" y="36" width="32" height="2" fill="white"/>
            </svg>''',
            
            'payment_terminal': '''<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
                <rect width="64" height="64" fill="#00695C" rx="8"/>
                <rect x="8" y="20" width="48" height="24" fill="#004D40" rx="4"/>
                <rect x="12" y="24" width="40" height="16" fill="#26A69A"/>
                <rect x="16" y="28" width="32" height="8" fill="#004D40" rx="2"/>
                <text x="32" y="33" text-anchor="middle" fill="white" font-family="Arial" font-size="6">CHIP</text>
            </svg>'''
        }
        
        for device_type, svg_content in svg_templates.items():
            filename = f"{device_type}.svg"
            svg_path = self.svg_dir / filename
            
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            icon = RestaurantIcon(
                name=f"{device_type.replace('_', ' ').title()}",
                device_type=device_type,
                pos_system=None,
                svg_path=str(svg_path),
                source_url="Generated Placeholder"
            )
            icons.append(icon)
        
        return icons
    
    def download_pos_system_icons(self) -> List[RestaurantIcon]:
        """Download specific POS system icons"""
        icons = []
        
        # Create POS system specific icons
        pos_colors = {
            'Clover': '#2E7D32',
            'Square': '#1565C0', 
            'Toast': '#D32F2F',
            'NCR': '#F57C00',
            'Micros': '#6A1B9A'
        }
        
        for pos_system, color in pos_colors.items():
            svg_content = f'''<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
                <rect width="64" height="64" fill="{color}" rx="6"/>
                <rect x="8" y="16" width="48" height="32" fill="{color}" opacity="0.8" rx="4"/>
                <text x="32" y="35" text-anchor="middle" fill="white" font-family="Arial" font-size="8" font-weight="bold">{pos_system}</text>
                <circle cx="32" cy="52" r="2" fill="white" opacity="0.7"/>
            </svg>'''
            
            filename = f"{pos_system.lower().replace(' ', '_')}_pos.svg"
            svg_path = self.svg_dir / filename
            
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            icon = RestaurantIcon(
                name=f"{pos_system} POS",
                device_type='pos_register',
                pos_system=pos_system,
                svg_path=str(svg_path),
                source_url="Generated POS System Icon"
            )
            icons.append(icon)
        
        return icons
    
    def save_icon_mapping(self, icons: List[RestaurantIcon]):
        """Save icon mapping to JSON file"""
        mapping = {}
        
        for icon in icons:
            key = f"{icon.device_type}_{icon.name.replace(' ', '_').lower()}"
            mapping[key] = {
                'name': icon.name,
                'device_type': icon.device_type,
                'pos_system': icon.pos_system,
                'svg_path': icon.svg_path,
                'png_path': icon.png_path,
                'source_url': icon.source_url
            }
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2)
        
        log.info(f"Saved {len(icons)} icon mappings to {self.metadata_file}")
    
    def download_all_icons(self) -> List[RestaurantIcon]:
        """Download icons from all sources"""
        all_icons = []
        
        log.info("Creating placeholder restaurant icons...")
        placeholder_icons = self.create_placeholder_icons()
        all_icons.extend(placeholder_icons)
        
        log.info("Creating POS system icons...")
        pos_icons = self.download_pos_system_icons()
        all_icons.extend(pos_icons)
        
        log.info("Attempting to download from external sources...")
        try:
            icons8_icons = self.download_icons8_icons()
            all_icons.extend(icons8_icons)
        except Exception as e:
            log.warning(f"Icons8 download failed: {e}")
        
        try:
            freepik_icons = self.download_freepik_icons()
            all_icons.extend(freepik_icons)
        except Exception as e:
            log.warning(f"Freepik download failed: {e}")
        
        # Save the mapping
        self.save_icon_mapping(all_icons)
        
        log.info(f"Total icons collected: {len(all_icons)}")
        return all_icons

def create_restaurant_icon_api(app):
    """Create FastAPI endpoints for restaurant icon management"""
    from fastapi import HTTPException
    from pydantic import BaseModel
    
    class IconLibraryResponse(BaseModel):
        icons: List[RestaurantIcon]
        total: int
        device_types: List[str]
        pos_systems: List[str]
    
    @app.get("/api/icons/restaurant", response_model=IconLibraryResponse)
    async def get_restaurant_icons():
        """Get restaurant technology icon library"""
        try:
            downloader = RestaurantIconDownloader()
            
            # Load existing icon mapping if available
            if downloader.metadata_file.exists():
                with open(downloader.metadata_file, 'r') as f:
                    mapping = json.load(f)
                
                icons = []
                for icon_data in mapping.values():
                    icon = RestaurantIcon(**icon_data)
                    icons.append(icon)
            else:
                # Generate icons if none exist
                icons = downloader.download_all_icons()
            
            device_types = list(set(icon.device_type for icon in icons))
            pos_systems = list(set(icon.pos_system for icon in icons if icon.pos_system))
            
            return IconLibraryResponse(
                icons=icons,
                total=len(icons),
                device_types=device_types,
                pos_systems=pos_systems
            )
            
        except Exception as e:
            log.error(f"Restaurant icon API error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/icons/restaurant/refresh")
    async def refresh_restaurant_icons():
        """Refresh restaurant icon library"""
        try:
            downloader = RestaurantIconDownloader()
            icons = downloader.download_all_icons()
            
            return {"message": "Restaurant icon library refreshed", "total": len(icons)}
            
        except Exception as e:
            log.error(f"Icon refresh error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

if __name__ == "__main__":
    # Demo usage
    downloader = RestaurantIconDownloader()
    icons = downloader.download_all_icons()
    
    print(f"Downloaded {len(icons)} restaurant icons")
    for icon in icons[:5]:  # Show first 5
        print(f"  - {icon.name} ({icon.device_type})")
