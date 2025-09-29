#!/usr/bin/env python3
"""
Enhanced runner for the chess dashboard
"""
from enhanced_main import EnhancedChessDashboard

if __name__ == "__main__":
    dashboard = EnhancedChessDashboard()
    # For production, disable debug mode
    import os
    debug_mode = os.environ.get('ENVIRONMENT', 'development') == 'development'
    dashboard.run(debug=debug_mode)