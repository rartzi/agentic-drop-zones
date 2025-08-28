---
name: Morning Debrief
allowed-tools: Bash, Read, Write
description: Transcribe morning debrief audio and analyze for engineering ideas and priorities
---

# Morning Debrief Analyzer

This prompt transcribes morning debrief audio recordings using OpenAI Whisper and analyzes the transcript to extract and organize key engineering ideas discussed. It creates a structured summary with the current date and quarter, identifies the top 3 priorities, lists all key ideas from the debrief, and generates novel extensions based on those ideas, and generates leading questions that can guide our work today with ideas for potential answers and next steps. Then it creates a transcript section with the full transcript of the debrief with every sentence as an individual item in a bulleted list. The output follows a clear hierarchical structure that makes it easy to reference during the workday. See the `Instructions` section for the detailed process. Output your results in a new markdown file with an alphanumeric + underscore name based on the original transcript file name.

## Prerequisites

- OpenAI Whisper must be installed
- If you encounter installation errors, STOP and notify the user:
  ```
  Whisper is not installed. Please run:
  uv tool install openai-whisper
  ```

## Variables

AUDIO_FILE_PATH: [[FILE_PATH]]
DEBRIEF_OUTPUT_DIR: agentic_drop_zone/morning_debrief_zone/debrief_output/<date_time>/
DEBRIEF_ARCHIVE_DIR: DEBRIEF_OUTPUT_DIR/drop_zone_file_archive/

## Instructions
- First, check if whisper is available by running: `which whisper`
- If whisper is not found, notify the user to install it with: `uv tool install openai-whisper`
- Create output directory: `DEBRIEF_OUTPUT_DIR/<date_time>/`
  - `date_time` is the current date and time in the format YYYY-MM-DD_HH-MM-SS
- Transcribe the audio file using: `whisper "[[FILE_PATH]]" --model tiny --language en --output_format txt --output_dir DEBRIEF_OUTPUT_DIR/`
  - The `--model tiny` is fast and suitable for English transcription
  - You can use `--model base` or `--model small` for better accuracy if needed
  - The transcription will generate a .txt file in the output directory
  - IMPORTANT: Run this command with a 5 minute timeout. If it doesn't finish, notify the user and stop.
- Read the generated transcript file (it will have the same base name as the audio file but with .txt extension)
- Read the generated transcript file
- Determine the current date and quarter (Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec)
- Analyze the transcript to identify all engineering ideas and priorities mentioned
- Extract the top 3 most important priorities from the discussion
- List all key ideas concisely, focusing on actionable engineering concepts
- Generate novel extensions by:
  - Combining related ideas in new ways
  - Identifying potential optimizations or improvements
  - Suggesting complementary features or approaches
  - Proposing innovative solutions based on the discussed concepts
  - Extrapolate from the key ideas to add your own tasteful extensions
  - Push the ideas further based on your own experience and knowledge
- Structure the output with clear sections and bullet points for readability
- Keep descriptions concise but informative
- Focus on actionable aspects
- IMPORTANT: Output your results in a new markdown file in the output directory: `DEBRIEF_OUTPUT_DIR/<date_time>/debrief_<QN>_<3 letter month>_<2 digit day>_<4 digit year>.md`
- Copy the original audio file to the output directory for reference: `cp AUDIO_FILE_PATH DEBRIEF_OUTPUT_DIR/<date_time>/original_audio.<ext>`
- IMPORTANT: Once you finish, open the new file with `code DEBRIEF_OUTPUT_DIR/<date_time>/debrief_<QN>_<3 letter month>_<2 digit day>_<4 digit year>.md`
- Ultra Think as you work through this process.
- When finished, move the original audio file to the archive: `mv AUDIO_FILE_PATH DEBRIEF_ARCHIVE_DIR/`

## Output Structure
The analysis should be formatted as follows:
1. **Title** - A descriptive title based on the debrief content
2. **Date** - Current date with quarter (e.g., "2025-01-29 (Q1 2025)")
3. **Top 3 Priorities** - Numbered list of the most important items
4. **Key Ideas** - Bulleted list of all ideas from the transcript
5. **Extensions** - Novel ideas derived from the key ideas
6. **Leading Questions** - Questions to guide today's work with potential answers
7. **Transcript** - Full transcript with each sentence as a bullet point

