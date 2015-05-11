Plot data:

    {
        "rcparams": {...},
        "rcparams_file": <string>,
        
        "title": <string>,
        
        "x_label": <string>,
        "x_labelpad": <int>,
        "x_min": <num>,
        "x_max": <num>,
        "x_maxitvls": <int>,
        "x_ticklocs": [<num>, ...],
        "x_log": <bool>,
        
        "y_label": <string>,
        "y_labelpad": <int>,
        "y_min": <num>,
        "y_max": <num>,
        "y_maxitvls": <int>,
        "y_ticklocs": [<num>, ...],
        "y_log": <bool>,
        
        "legend": <bool>,
        "legend_ncol": <int>,
        "legend_loc": <loc string>,
        "legend_bbox": <quadruple>,
        
        "figsize": (<width>, <height>),
        "dpi": <int>,
        "tight_layout": <bool>,
        "tight_layout_rect": <quadruple>,
        
        "series": [
            {
                "name": <string>,
                
                "format": "normal" (default) | "polyfit" | "points",
                "polydeg": <int>,
                
                "points": [(<x>, <y>), ...],
                
                "errdata": [(<low_err_delta>, <high_err_delta>), ...] or None,
                
                "color": <string>,
                "linestyle": <string> (default '-'),
                "marker": <string> (default 'o'),
                "hollow_markers": <bool>,
                "marker_border": <bool>,
                "dashes": <int list or None>,
            },
            ...
        ],
    }
