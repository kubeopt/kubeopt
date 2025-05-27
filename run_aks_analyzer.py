#!/usr/bin/env python3
from app import app, update_base_template, update_results_template, update_index_template
from app import update_implementation_template, create_static_dirs
from app import add_chart_data_route, add_demo_update_route, add_auto_update_feature
import logging

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Setting up AKS Cost Optimization Web App with Dynamic Charts...")
    
    # Create templates and directories
    update_base_template()
    update_index_template()
    update_results_template()
    update_implementation_template()
    create_static_dirs()
    
    # Add API routes
    add_chart_data_route(app)
    add_demo_update_route(app)
    
    # Start background data updates
    bg_thread = add_auto_update_feature()
    
    logger.info("Starting web server at http://127.0.0.1:5000/")
    logger.info("Press Ctrl+C to exit")
    
    # Run the application
    app.run(debug=True, use_reloader=False)  # use_reloader=False prevents duplicate background threads
