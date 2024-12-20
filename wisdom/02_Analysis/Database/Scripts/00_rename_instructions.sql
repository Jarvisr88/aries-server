-- Table Rename Process Instructions
-- Generated: 2024-12-16

/*
STEP 1: Configure the rename process
---------------------------------
Update these settings in rename_config.settings:

UPDATE rename_config.settings 
SET setting_value = 'public'        -- Change to your target schema
WHERE setting_key = 'target_schema';

UPDATE rename_config.settings 
SET setting_value = 'tbl_'          -- Change if your prefix is different
WHERE setting_key = 'prefix_to_remove';

UPDATE rename_config.settings 
SET setting_value = '50'            -- Adjust batch size if needed
WHERE setting_key = 'batch_size';

STEP 2: Run Validation
--------------------
1. Run: \i '05_pre_rename_validation.sql'
2. Review the validation results:
   - Fix any ERRORs before proceeding
   - Review WARNINGs and ensure they're acceptable
   - Check dependencies and potential impacts

STEP 3: Perform Rename
--------------------
1. Run: \i '06_rename_with_logging.sql'
2. Monitor the progress in rename_progress table
3. Check logs in table_rename_log for details

STEP 4: Verify Changes
--------------------
-- Check renamed tables
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_schema = (
    SELECT setting_value 
    FROM rename_config.settings 
    WHERE setting_key = 'target_schema'
)
ORDER BY table_name;

-- Check rename operation logs
SELECT * FROM public.table_rename_log 
WHERE created_at >= (current_timestamp - interval '1 hour')
ORDER BY created_at DESC;

ROLLBACK IF NEEDED
----------------
If you need to rollback, the rename script includes commented rollback commands
at the bottom. Uncomment and run those commands.

CLEANUP
-------
-- Optional: Clean up old logs (keeps last 30 days by default)
DELETE FROM public.table_rename_log 
WHERE created_at < (current_timestamp - interval '30 days');
*/
