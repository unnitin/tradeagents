Cursor and openAI agents to keep the following in mind
1. Understand and obey specs in docs - system design, api-spec and userflows are critical for context
2. Implement the code as a monolith of microservices 
3. Explain when best practices contradict the specs with reasons
4. Simple commented code preferred over complicated multi-level inheritance code 
5. Encapsulate small, testable code in functions so we can cover them with tests
6. For any new module being developed, first document the expected behavior as tests then develop functionality
7. Use small feature pipelines and merge to main often
8. For every API endpoint, add a docstring describing expected inputs (query params/body fields) and their purpose so agents and maintainers stay aligned
