[Deutsch](STAGE499_WFM_SOURCE_OUTLINE_EVENT_SORT_PANEL_WIDTH.md) | [English](STAGE499_WFM_SOURCE_OUTLINE_EVENT_SORT_PANEL_WIDTH.en.md)

# Stage 499 – WFM Source Outline, Event Procedures, and Component Panel

Refines WFM editor navigation: under **Procedures**, `__init__` appears before `__del__`, followed by case-insensitive alphabetical ordering; under **Functions**, `__main__` appears first. Natural sorting places `Button2_onClick` before `Button10_onClick`. `Qt.UserRole` continues to reference the original source line, so clicking an outline entry navigates to the actual declaration. The editor can insert or navigate to event procedures, and the left component/properties panel is adjusted for consistent width and interaction. Tests focus on sorting, mapping, and panel layout; native Qt confirmation is still necessary.
