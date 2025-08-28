# Echo Command

Echo the contents of the file at DROPPED_FILE_PATH and provide a brief summary.

## Variables

DROPPED_FILE_PATH: [[FILE_PATH]]
DROPPED_FILE_PATH_ARCHIVE: agentic_drop_zone/echo_zone/drop_zone_file_archive/

## Workflow
1. Read the file contents at DROPPED_FILE_PATH
2. Write out the file in between a markdown code block
3. Below log the total number of characters in the file and the file name
4. Move the file to the archive: `mv DROPPED_FILE_PATH DROPPED_FILE_PATH_ARCHIVE/`

## Example Output Format

```
<file_contents>

total characters: <number_of_characters>
file name: <file_name>
```
