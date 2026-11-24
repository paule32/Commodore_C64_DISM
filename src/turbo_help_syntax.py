# -*- coding: utf-8 -*-
"""Stage 687: shared THLP directive recognition (GUI-independent)."""
from __future__ import annotations

import re

# Only known commands are colored; %topic-extra and arbitrary text are not.
HELP_DIRECTIVE_PATTERN = re.compile(
    r"(?<![\w%])%(?:topic|include|ref|anchor|link)\b", re.IGNORECASE
)
