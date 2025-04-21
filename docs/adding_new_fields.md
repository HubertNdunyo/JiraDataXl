# How to Add a New JIRA Field to the Sync Process

This document outlines the steps required to add a new custom field from JIRA to the data synchronization pipeline, ensuring it's fetched from JIRA, stored in the database, and handled correctly by the application code.

**Prerequisites:**

*   Identify the JIRA Custom Field ID (e.g., `customfield_XXXXX`).
*   Determine the expected data type (string, integer, boolean, datetime).

**Steps:**

1.  **Update Field Mapping Configuration (`config/field_mappings.json`):**
    *   Choose a logical, descriptive name for the field within the application (e.g., `my_new_field`).
    *   Locate the appropriate `field_groups` section (e.g., `client_info`, `order_details`) or create a new one if necessary.
    *   Add a new entry for your logical field name inside the `"fields": { ... }` object of the chosen group.
    *   Define the `type` (e.g., `"string"`, `"integer"`, `"boolean"`, `"datetime"`).
    *   For each relevant JIRA instance (`"instance_1"`, `"instance_2"`), add an object specifying the JIRA `"field_id"` and a descriptive `"name"`.

    ```json
    "field_groups": {
      "your_group": {
        "description": "...",
        "fields": {
          "...": { ... },
          "my_new_field": {
            "type": "string", // Or integer, boolean, datetime
            "description": "Description of the new field",
            "instance_1": {
              "field_id": "customfield_XXXXX",
              "name": "JIRA Field Name Instance 1"
            },
            "instance_2": {
              "field_id": "customfield_YYYYY", // Can be the same or different
              "name": "JIRA Field Name Instance 2"
            }
          }
        }
      }
    }
    ```

2.  **Update Database Schema:**
    *   Determine the database column name. The convention is typically `ndpu_` + logical field name (e.g., `ndpu_my_new_field`).
    *   Choose the corresponding SQL data type (`TEXT`, `INTEGER`, `BOOLEAN`, `TIMESTAMP`).
    *   Connect to the PostgreSQL database (`jira_data_pipeline`) using `psql` or another tool.
    *   Add the column to the `jira_issues_v2` table:
        ```sql
        ALTER TABLE jira_issues_v2 ADD COLUMN ndpu_my_new_field TEXT; -- Use appropriate type
        ```

3.  **Update Database Documentation (`docs/database_schema.md`):**
    *   Edit the `CREATE TABLE jira_issues_v2` definition in this file.
    *   Add the new column definition in the correct location.
        ```sql
        CREATE TABLE jira_issues_v2 (
            ...
            ndpu_my_new_field TEXT, -- Add new column here
            ...
        );
        ```

4.  **Update Application Code:**

    *   **Constants (`core/db/constants.py`):**
        *   Edit the `ISSUE_COLUMNS` list.
        *   Add the new database column name (e.g., `'ndpu_my_new_field'`) to the list. **Crucially, ensure the order in this list exactly matches the order you intend for the data tuple created later.**

    *   **Issue Processing (`core/jira/jira_issues.py`):**
        *   Edit the `process_issue` method.
        *   Add a line to extract the field's value from the raw JIRA `fields` dictionary using its JIRA custom field ID:
            ```python
            my_new_field_value = self.field_processor.extract_field_value(fields, 'customfield_XXXXX')
            ```
        *   Locate the `record = (...)` tuple construction near the end of the method.
        *   Insert the `my_new_field_value` variable into the tuple at the position corresponding to its column name's position in the `ISSUE_COLUMNS` list (from `constants.py`).

    *   **Database Insertion (`core/db/db_issues.py`):**
        *   Edit the `create_issues_table` function (around lines 28-59). Add the new column definition (`ndpu_my_new_field TEXT`) to the `CREATE TABLE IF NOT EXISTS` statement. This ensures the code reflects the schema even if the table already exists.
        *   Edit the `batch_insert_issues` function. Locate the `ON CONFLICT (issue_key) DO UPDATE SET` clause (around lines 111-139).
        *   Add a line to update the new column:
            ```sql
            ndpu_my_new_field = EXCLUDED.ndpu_my_new_field,
            ```

5.  **Testing (Recommended):**
    *   Modify `utils/scripts/test_single_issue.py`.
    *   Update `ISSUE_KEY_TO_TEST` to an issue key known to have data in the new field.
    *   Run the script (`python3 utils/scripts/test_single_issue.py`).
    *   Verify that:
        *   The new JIRA field ID is listed in the "Fields requested from JIRA" log message.
        *   The raw data for the field is printed correctly.
        *   The processed data dictionary shows the correct value for the new field.
        *   The "Processed tuple length matches expected column count" message appears.

6.  **Commit and Push:**
    *   Add all modified files to Git staging:
        ```bash
        git add config/field_mappings.json docs/database_schema.md core/db/constants.py core/jira/jira_issues.py core/db/db_issues.py
        ```
    *   Commit the changes with a descriptive message:
        ```bash
        git commit -m "Feat: Add support for 'My New Field' (customfield_XXXXX)"
        ```
    *   Push the changes to the remote repository:
        ```bash
        git push origin master
        ```

Following these steps ensures that the new field is correctly configured, the database schema is updated, and the application code fetches, processes, and stores the data appropriately.