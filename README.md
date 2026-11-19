# Ticket to MR Agent

An AI-assisted GitLab agent that turns a labeled issue into a draft merge request. It validates the issue, creates an implementation plan, writes code in an isolated workspace, runs tests, attempts fixes, and opens a merge request through the GitLab API.

## How It Works

1. Create or update a GitLab issue and add the `ai-ready` label.
2. GitLab sends an issue webhook to the Flask server.
3. The agent checks whether the issue contains enough information.
4. It posts an implementation plan to the issue.
5. It clones the project into an isolated workspace and asks the configured model to write code.
6. The project test suite is run. Failed changes can be sent back to the model for up to three configured fix attempts.
7. If tests pass, the agent pushes an `ai/issue-<iid>` branch and creates a draft merge request.
8. Issue labels are updated to show `ai-in-progress`, `ai-review`, or `ai-failed` status.

## Features

- GitLab issue webhook integration with secret-token validation
- AI issue-quality checks before implementation starts
- Generated implementation specifications posted on the issue
- Isolated Git workspaces for each issue
- Configurable Ollama models for issue checks, specifications, code generation, and fixes
- Automatic test execution and fix retries
- Branch pushing and draft merge request creation
- Issue comments and label-based status updates
- Duplicate-run protection for the same issue

## Requirements

- Python 3.10 or newer
- Git
- A GitLab personal or project access token
- A running [Ollama](https://ollama.com/) server
- An Ollama model that is suitable for code generation

## Installation

Clone the repository:

```bash
git clone https://github.com/ayan84956-source/ticket-to-mr-agent.git
cd ticket-to-mr-agent
```

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Pull the default model and start Ollama:

```bash
ollama pull qwen2.5-coder:3b
ollama serve
```

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure the environment variables:

```dotenv
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your-gitlab-access-token
WEBHOOK_SECRET=a-long-random-secret
OLLAMA_URL=http://localhost:11434
CLOUD_API_KEY=optional-cloud-provider-key
```

Keep `.env` private and never commit real credentials.

The behavior and model settings are controlled by `config.yaml`:

```yaml
labels:
  trigger: ai-ready
  in_progress: ai-in-progress
  failed: ai-failed
  review: ai-review

agent:
  max_attempts: 3
  work_dir: C:/agent_work/runs

models:
  default:
    provider: ollama
    name: qwen2.5-coder:3b
  check_issue: {}
  write_spec: {}
  write_code: {}
  fix_code: {}
```

For individual AI jobs, add provider-specific settings alongside the job name. For example:

```yaml
write_code:
  provider: ollama
  name: qwen2.5-coder:7b
  temperature: 0.2
  num_ctx: 8192
```

Update `agent.work_dir` to a writable absolute path on the machine running the server.

## GitLab Setup

Create the following labels in the target GitLab project:

- `ai-ready` — starts the agent
- `ai-in-progress` — agent is processing the issue
- `ai-failed` — processing failed or tests did not pass
- `ai-review` — a draft merge request was created

The GitLab token needs permission to:

- Read the issue
- Add comments and manage labels
- Clone the project
- Push branches
- Create merge requests

In GitLab, add a project webhook with:

- URL: the public URL forwarded to `http://127.0.0.1:8000/webhook`
- Secret token: the value of `WEBHOOK_SECRET`
- Trigger: **Issues events**

For local development, expose the server with a tool such as Cloudflare Tunnel or ngrok.

## Running the Server

Start the webhook server:

```bash
python server.py
```

The service listens on `127.0.0.1:8000` by default.

To start work for an issue manually:

```bash
python agent.py <project-id> <issue-iid>
```

For example:

```bash
python agent.py 123 42
```

Then add the `ai-ready` label to issue 42 in project 123.

## Usage

Write a clear issue containing:

- The requested behavior
- Relevant files or components
- Acceptance criteria
- Any useful context or constraints

Adding `ai-ready` causes the webhook to run the agent. The issue will receive a comment with the generated plan, test progress or failures, and the draft merge request URL when successful.

If the issue is incomplete, the agent asks for more information and removes the trigger label so it does not repeatedly start.

## Tests

Run the test suite:

```bash
pytest
```

The agent determines and runs the test suite inside the target project's cloned workspace.

## Project Structure

```text
agent.py             Main issue-to-merge-request workflow
server.py            Flask webhook server
config.yaml          Labels, retry limits, workspace, and model settings
ai_steps/            Issue checks, specs, code generation, and fix loops
core/                GitLab, Git, workspace, model, and test helpers
prompts/             Prompt templates
helpers/             Additional utility code
try_*.py             Development and integration scripts
```

## Limitations

- The model provider is currently implemented for Ollama; cloud provider support is not yet available.
- The agent should be reviewed by a human before changes are merged.
- The quality of generated changes depends on the repository, issue details, test coverage, and selected model.
- Production deployments should use a secure public endpoint and proper process management.

## Contributing

Contributions are welcome. Open an issue describing a bug or improvement, then submit a merge request with tests where applicable.

## Project Status

Active development.
