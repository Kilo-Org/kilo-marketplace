---
name: add-documentation
description: >-
  This skill should be used when the user wants to add documentation to a project.
  It helps create comprehensive documentation including README files, API documentation,
  code comments, and other documentation artifacts. Use when the user asks to document
  code, create documentation, or improve project documentation.
license: Complete terms in LICENSE.txt
metadata:
  category: development
---

# Add Documentation

This skill provides a systematic approach to adding documentation to projects. It helps create clear, comprehensive, and well-structured documentation that improves code maintainability and user understanding.

## When to Use This Skill

Use this skill when:
- The user asks to "add documentation" or "document this project"
- Creating README files for new or existing projects
- Writing API documentation
- Adding inline code comments
- Creating user guides or tutorials
- Documenting configuration options

## Documentation Types

### 1. README Files

Every project should have a README.md file that includes:
- **Project name and description**: Clear explanation of what the project does
- **Installation instructions**: Step-by-step guide to get started
- **Usage examples**: Common use cases with code examples
- **Configuration options**: Available settings and their defaults
- **Contributing guidelines**: How others can contribute
- **License information**: Usage rights and restrictions

### 2. API Documentation

For libraries and APIs, document:
- **Function/method signatures**: Parameters, return types, exceptions
- **Usage examples**: Code snippets showing common patterns
- **Type definitions**: Interfaces, types, and their properties
- **Authentication**: How to authenticate requests (if applicable)
- **Rate limits and quotas**: Usage restrictions

### 3. Code Comments

Add meaningful comments that:
- Explain **why** code exists, not just **what** it does
- Document complex algorithms or business logic
- Mark TODOs, FIXMEs, and important notes
- Provide context for future maintainers

### 4. Architecture Documentation

For larger projects, include:
- **System overview**: High-level architecture diagram
- **Component descriptions**: What each module does
- **Data flow**: How information moves through the system
- **Deployment guide**: How to deploy the application

## Documentation Best Practices

### Clarity and Conciseness
- Use simple, direct language
- Avoid jargon unless necessary (and explain it when used)
- Keep sentences and paragraphs short
- Use bullet points for lists

### Code Examples
- Provide working, tested code examples
- Include both simple and advanced use cases
- Show expected output when relevant
- Keep examples up-to-date with the codebase

### Organization
- Use consistent heading hierarchy
- Include a table of contents for long documents
- Group related information together
- Provide navigation links between related documents

### Maintenance
- Keep documentation close to the code it documents
- Update documentation when code changes
- Review documentation regularly for accuracy
- Include documentation in code review processes

## Documentation Workflow

1. **Analyze the project**: Understand the codebase structure and purpose
2. **Identify documentation gaps**: Determine what documentation is missing or outdated
3. **Prioritize documentation needs**: Focus on the most critical areas first
4. **Create/update documentation**: Write clear, comprehensive documentation
5. **Review and refine**: Ensure accuracy and clarity
6. **Integrate with project**: Add documentation files to the appropriate locations

## Output Formats

This skill can produce documentation in various formats:
- **Markdown (.md)**: For README files, wikis, and static site generators
- **JSDoc/TSDoc**: For JavaScript/TypeScript code comments
- **Docstrings**: For Python documentation
- **Javadoc**: For Java documentation
- **OpenAPI/Swagger**: For REST API documentation

## Tools and Resources

Consider using these documentation tools:
- **JSDoc/TSDoc**: JavaScript/TypeScript documentation generators
- **Sphinx**: Python documentation framework
- **Swagger/OpenAPI**: API documentation
- **Docusaurus**: Documentation websites
- **Storybook**: UI component documentation

## Example Usage

When asked to add documentation, the skill will:

1. Analyze the existing codebase structure
2. Identify the primary language(s) and frameworks used
3. Determine appropriate documentation format(s)
4. Create comprehensive documentation following best practices
5. Ensure documentation is placed in the correct location(s)

---

Remember: Good documentation is as important as good code. It helps users understand how to use your project and helps developers maintain it over time.
