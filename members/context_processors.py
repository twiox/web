def nav_section(request):
    """Which entry of the main navigation is highlighted, from the URL.

    The landing page, the Impressum and the privacy page belong to no section.
    """
    path = request.path
    if path.startswith("/interessierte/"):
        section = "interested"
    elif path.startswith("/veranstalter/"):
        section = "organizers"
    elif path in ("/", "/impressum") or path.startswith("/datenschutz"):
        section = ""
    else:
        section = "members"  # member area, board, trainer pages, login
    return {"nav_section": section}
