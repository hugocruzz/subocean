subocean/
│
├── src/
│   ├── core/
│   │   ├── data_model.py        # Core data structures and validation
│   │   └── profile.py           # Profile class handling dataset
│   │
│   ├── preprocessing/
│   │   ├── cleaner.py           # Data cleaning and validation
│   │   ├── rsd_processor.py     # Relative Standard Deviation processing
│   │   └── error_handler.py     # Error Standard processing
│   │
│   ├── visualization/
│   │   ├── plot_manager.py      # Plot creation and management
│   │   ├── interactive.py       # Interactive plotting features
│   │   └── exporters.py         # Plot export utilities
│   │
│   ├── gpt_interface/
│   │   ├── prompt_handler.py    # GPT prompt management
│   │   ├── command_parser.py    # Natural language command parsing
│   │   └── response_formatter.py # GPT response formatting
│   │
│   └── utils/
│       ├── config_loader.py     # Configuration management
│       ├── logger.py            # Logging utilities
│       └── validators.py        # Data validation utilities
│
├── config/
│   ├── schema.yaml             # Data schema definition
│   ├── plots.yaml              # Plot configurations
│   └── gpt_prompts.yaml        # GPT prompt templates
│
├── tests/
│   ├── test_core/
│   ├── test_preprocessing/
│   ├── test_visualization/
│   └── test_gpt_interface/
│
└── examples/
    ├── basic_usage.ipynb
    ├── interactive_plotting.ipynb
    └── gpt_integration.ipynb