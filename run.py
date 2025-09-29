#!/usr/bin/env python3
"""
Kiren Chess Dashboard - Interactive opponent analysis and tournament tracking
"""
from enhanced_main import EnhancedChessDashboard
import os

if __name__ == "__main__":
    dashboard = EnhancedChessDashboard()
    debug_mode = os.environ.get('ENVIRONMENT', 'development') == 'development'
    dashboard.run(debug=debug_mode)