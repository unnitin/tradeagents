this file describes aspirations for the composer module

functionality in composer module
1. register different strategies
    1.1. access the `strategies/` module and initiate objects of the classes
    1.2. will need to access configurations in a yaml contained in `config/` (to be created)
2. define methods to combine various strategies
    2.1. note a strategy may not need to be combined to be executable (eg quiver strategies)
3. any strategy outputted from this module will need to plug into back testing and then eventually to execution 
flow will be data -> composer (reading from config, strategies) -> backtester -> execution