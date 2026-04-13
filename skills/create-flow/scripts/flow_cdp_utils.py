import asyncio


async def cdp_click(tab, x: float, y: float):
    """
    Hardcore CDP Click: Adjusts for High-DPI (Retina) displays via devicePixelRatio,
    and dispatches exact MouseMoved -> MousePressed -> MouseReleased events using
    native floats and CDP enums to bypass React/Shadow-DOM event swallowing.
    """
    import nodriver.cdp.input as input_cdp

    # Adjust for High-DPI displays (Critical for Macs)
    dpr = await tab.evaluate("window.devicePixelRatio")
    x_scaled, y_scaled = float(x) / float(dpr), float(y) / float(dpr)

    # Emulate realistic interaction
    await tab.send(input_cdp.dispatch_mouse_event("mouseMoved", x=x_scaled, y=y_scaled))
    await asyncio.sleep(0.1)  # Give React/Vue time to register hover/focus states

    await tab.send(
        input_cdp.dispatch_mouse_event(
            "mousePressed",
            x=x_scaled,
            y=y_scaled,
            button=input_cdp.MouseButton("left"),
            buttons=1,
            click_count=1,
        )
    )

    # buttons MUST be 0 on release, otherwise React ignores the click
    await tab.send(
        input_cdp.dispatch_mouse_event(
            "mouseReleased",
            x=x_scaled,
            y=y_scaled,
            button=input_cdp.MouseButton("left"),
            buttons=0,
            click_count=1,
        )
    )


async def open_incognito_context(browser, url: str = "about:blank"):
    """
    Native Context-ID Logic: Uses CDP create_browser_context to spawn a completely
    isolated, incognito-like environment per tab. AppleScript is blind to these,
    but nodriver CDP handles them perfectly.
    """
    incognito_tab = await browser.create_context(
        url=url,
        new_window=True,
        dispose_on_detach=True,  # Clears session data when closed
    )
    return incognito_tab


def get_tabs_snapshot(browser) -> set:
    """
    Returns a snapshot of current target IDs, used before triggering a target="_blank" click.
    """
    return {t.target_id for t in browser.tabs}


async def find_new_tab(browser, old_targets: set, timeout: float = 2.0):
    """
    State-Tracking for target="_blank": Compares current tabs against a snapshot
    to find and activate newly opened tabs.
    """
    elapsed = 0.0
    while elapsed < timeout:
        new_tabs = [t for t in browser.tabs if t.target_id not in old_targets]
        if new_tabs:
            new_tab = new_tabs[0]
            await new_tab.bring_to_front()
            return new_tab
        await asyncio.sleep(0.1)
        elapsed += 0.1
    return None


async def get_accessibility_tree(tab):
    """
    Screen-Reader DOM Trap Bypass: Retrieves the Accessibility (AX) Tree to find
    elements that are genuinely exposed to the user, ignoring visually hidden honeypots.
    """
    import nodriver.cdp.accessibility as ax_cdp

    ax_tree = await tab.send(ax_cdp.get_full_ax_tree())

    visible_nodes = [
        node
        for node in ax_tree.nodes
        if not node.ignored and any(prop.name == "name" for prop in node.properties)
    ]
    return visible_nodes


async def get_raw_unfiltered_dom_with_hidden(tab):
    """
    Absolute Visibility Bypass (The "See Everything" Protocol):
    Retrieves the complete, raw, flattened DOM tree natively via CDP.
    Unlike standard get_content() or the Accessibility Tree, this pierces through
    Shadow DOMs, Iframes, and exposes EVERY element (including display:none,
    visibility:hidden, 0x0 size tracking pixels like batBeacon, and honeypots).
    """
    import nodriver.cdp.dom as dom

    # Request the full flattened document: depth=-1 gets all nested children,
    # pierce=True pierces through Shadow DOM and iframes.
    flattened_nodes = await tab.send(dom.get_flattened_document(depth=-1, pierce=True))

    return flattened_nodes


async def find_hidden_tracking_pixels_and_honeypots(tab):
    """
    Specifically targets and extracts elements that are intentionally hidden
    from the user (display:none, visibility:hidden, or width/height 0) but
    exist in the DOM. Excellent for detecting bot-traps and tracking beacons.
    """
    nodes = await get_raw_unfiltered_dom_with_hidden(tab)
    hidden_elements = []

    for node in nodes:
        # Check node attributes for hidden styles or 0x0 dimensions
        if getattr(node, "attributes", None):
            attrs = node.attributes
            # attributes is a flat list: ["id", "batBeacon...", "style", "display: none; width: 0px..."]
            attr_dict = {attrs[i]: attrs[i + 1] for i in range(0, len(attrs), 2)}

            is_hidden = False
            style = attr_dict.get("style", "").lower()

            if "display: none" in style or "visibility: hidden" in style:
                is_hidden = True
            elif attr_dict.get("width") == "0" and attr_dict.get("height") == "0":
                is_hidden = True
            elif "width: 0px" in style and "height: 0px" in style:
                is_hidden = True
            elif attr_dict.get("type") == "hidden":
                is_hidden = True

            if is_hidden:
                hidden_elements.append(
                    {
                        "node_id": node.node_id,
                        "node_name": node.node_name,
                        "id": attr_dict.get("id", ""),
                        "class": attr_dict.get("class", ""),
                        "src": attr_dict.get("src", ""),
                        "style": style,
                    }
                )

    return hidden_elements
