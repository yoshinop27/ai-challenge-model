# Development Workflow Documentation

This document outlines the standard workflow for completing and deploying a story.

1. Pull a Story from Jira and Assign to Yourself

Navigate to the project board in Jira.

Select a story from the Backlog or To Do column.

Review the description and acceptance criteria.

Assign the story to yourself to indicate ownership.

2. Move the Story to “In Progress”

Once you begin active development, move the story to In Progress.

Create a feature branch using a consistent naming convention (e.g., feature/JIRA-123-short-description).

Begin implementation.

3. Complete the Story According to Acceptance Criteria

Implement the required functionality.

Ensure all acceptance criteria are fully satisfied.

Follow coding standards and project conventions.

Add or update:

- Unit tests
- Integration tests (if applicable)
- Relevant documentation

4. Create a Pull Request (PR)

Open a Pull Request targeting the development branch.
Push your feature branch to the remote repository.

Open a Pull Request targeting the development branch.

In the PR description, include:

Jira story reference (e.g., JIRA-123)

Summary of changes

Screenshots (if UI-related)

Testing notes

Any migration or deployment considerations

5. Verify All Tests Pass

Confirm:

All automated tests pass locally.

CI/CD pipeline checks succeed.

No linting or formatting errors remain.

Address any failed checks before requesting review.

6. Human Approval and Merge to Development

Request review from the appropriate team member(s).

Respond to feedback and make necessary revisions.

Once approved:

Merge the PR into the development branch.

Ensure the Jira story is updated accordingly (e.g., moved to “Ready for Deploy” or similar status).

7. Deploy to Development Server

Trigger the deployment pipeline (if automated) or deploy manually per project standards.

Verify the feature is successfully deployed to the development environment.

Perform basic smoke testing to confirm expected behavior.

Update Jira status to reflect deployment completion.
