# Agentic Drop Zone System - Flow Diagram

## Main System Flow

```mermaid
graph TD
    %% File System Events
    A[User Drops File] --> B[Python Watchdog<br/>Observer Pattern]
    B --> C[Pattern Matching<br/>drops.yaml + Pydantic]

    %% Zone Routing
    C --> D1[Echo Zone<br/>*.txt → echo.md]
    C --> D2[Image Generation<br/>*.txt,*.md → create_image.md]
    C --> D3[Training Data<br/>*.csv,*.jsonl → more_training_data.md]
    C --> D4[Morning Debrief<br/>Audio → morning_debrief.md]
    C --> D5[Finance Zone<br/>*.csv → finance_categorizer.md]

    %% Claude Code SDK Integration
    D1 --> E[ClaudeSDKClient<br/>bypassPermissions: true]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E

    %% AWS Bedrock Authentication
    E --> F[AWS Bedrock<br/>~/.aws/credentials<br/>sonnet-4 model]

    %% Tool Access & Execution
    F --> G[Full Tool Access<br/>Bash, Read, Write, Glob, Grep]
    G --> H[Rich Streaming Panels<br/>Real-time Console Output]

    %% Styling
    classDef zoneNode fill:#e3f2fd
    classDef sdkNode fill:#f3e5f5
    classDef awsNode fill:#e8f5e8
    classDef toolNode fill:#fff3e0

    class D1,D2,D3,D4,D5 zoneNode
    class E sdkNode
    class F awsNode
    class G toolNode
```

## Use Case Specific Workflows

### 1. Echo Zone (Simple Test)
```mermaid
graph LR
    A[Drop *.txt] --> B[echo.md] --> C[Simple Echo] --> D[Console Display]
```

### 2. Image Generation (Parallel Processing)
```mermaid
graph TD
    A[Drop *.txt with prompts] --> B[Claude Code: Bash Tool<br/>Parse prompt array with regex]
    B --> C[Bash: Create timestamped dir<br/>YYYY-MM-DD_HH-MM-SS]
    C --> D[Bash: Parallel background jobs<br/>& operator + PID tracking]

    D --> E1[Job 1: python tools/vertex_ai_image_generator.py<br/>--aspect-ratio 16:9]
    D --> E2[Job 2: python tools/vertex_ai_image_generator.py<br/>--aspect-ratio 16:9]
    D --> E3[Job N: python tools/vertex_ai_image_generator.py<br/>--aspect-ratio 16:9]

    E1 --> F[Google Cloud Vertex AI<br/>ImageGenerationModel.from_pretrained<br/>imagen-4.0-ultra-generate-preview-06-06]
    E2 --> F
    E3 --> F

    F --> G[Save JPG Files<br/>base64 decode + file write]
    G --> H[Bash: wait $pid<br/>Track job completion]
    H --> I[Rich Console: Success/Failure Report<br/>File sizes + error details]
    I --> J[Bash: open $output_dir<br/>macOS Finder integration]
```

### 3. Training Data Generation
```mermaid
graph LR
    A[Drop *.csv/*.jsonl] --> B[Analyze Patterns] --> C[Generate Synthetic Data] --> D[Export Enhanced Dataset]
```

### 4. Morning Debrief (Audio Processing)
```mermaid
graph LR
    A[Drop Audio File<br/>*.mp3, *.wav, *.m4a] --> B[Claude Code: Bash Tool<br/>whisper --model tiny --language en] --> C[Claude Code: Analysis<br/>Extract engineering ideas] --> D[Claude Code: Write Tool<br/>Generate markdown report] --> E[Bash: mkdir + mv<br/>Archive original file]
```

### 5. Finance Categorization
```mermaid
graph LR
    A[Drop *.csv Transactions] --> B[Parse Data] --> C[ML Categorization] --> D[Export Results]
```

## Technology Stack & Authentication Flow

```mermaid
graph TD
    A[uv run sfs_agentic_drop_zone.py] --> B[Python Dependencies<br/>claude-code-sdk, watchdog, pydantic, rich]

    B --> C[Environment Check<br/>CLAUDE_CODE_USE_BEDROCK=1]
    C --> D[AWS Authentication<br/>~/.aws/credentials]
    C --> E[Google Cloud Auth<br/>service-account-key.json]

    D --> F[ClaudeSDKClient.create<br/>permission_mode: bypassPermissions<br/>model: us.anthropic.claude-sonnet-4]
    E --> G[Vertex AI Client<br/>ImageGenerationModel.from_pretrained<br/>imagen-4.0-ultra-generate-preview-06-06]

    H[Watchdog Observer<br/>FileSystemEventHandler] --> I[Pydantic Validation<br/>drops.yaml → DropsConfig]
    I --> J[Template Loading<br/>.claude/commands/*.md]
    J --> F

    F --> K[Tool Execution<br/>Bash, Read, Write, Glob, Grep]
    G --> L[Direct Python Invocation<br/>vertex_ai_image_generator.py]

    K --> M[Rich Streaming Output<br/>Panels + Progress Bars]
    L --> M
```

## Technology Implementation Summary:

| Use Case | File Types | Technology Stack | Tool Invocations | Output |
|----------|------------|------------------|------------------|---------|
| **Echo** | `*.txt` | ClaudeSDKClient → AWS Bedrock | Simple prompt processing | Rich console display |
| **Image Generation** | `*.txt`, `*.md` | ClaudeSDKClient → Bash → Python subprocess | `python tools/vertex_ai_image_generator.py --aspect-ratio 16:9` | Parallel JPG files + completion report |
| **Training Data** | `*.csv`, `*.jsonl` | ClaudeSDKClient → Read/Write tools | Read CSV → Generate synthetic data → Write enhanced dataset | Enhanced dataset files |
| **Morning Debrief** | Audio files | ClaudeSDKClient → Bash → Whisper | `whisper --model tiny --language en` | Markdown transcription + analysis |
| **Finance** | `*.csv` | ClaudeSDKClient → Read/Write tools | Read CSV → ML categorization → Write results | Categorized transaction files |

## Key Technology Features:

- ✅ **File Monitoring**: Python Watchdog with Observer pattern
- ✅ **Configuration**: Pydantic validation of drops.yaml
- ✅ **Agent Execution**: ClaudeSDKClient with `bypassPermissions: true`
- ✅ **Authentication**: AWS Bedrock via `~/.aws/credentials`
- ✅ **Image Generation**: Direct Python invocation of `tools/vertex_ai_image_generator.py`
- ✅ **Parallel Processing**: Bash background jobs with PID tracking (`&` operator + `wait`)
- ✅ **Console Output**: Rich streaming panels with real-time progress
- ✅ **Tool Access**: Full suite (Bash, Read, Write, Glob, Grep)
- ✅ **Template System**: Variable substitution (`[[FILE_PATH]]` → actual path)
- ✅ **Error Handling**: Try/catch with detailed error reporting