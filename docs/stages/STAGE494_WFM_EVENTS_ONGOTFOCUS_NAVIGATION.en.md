[Deutsch](STAGE494_WFM_EVENTS_ONGOTFOCUS_NAVIGATION.md) | [English](STAGE494_WFM_EVENTS_ONGOTFOCUS_NAVIGATION.en.md)

# Stage 494 – OnGotFocus and Double-Click Navigation in WFM Events

The form Properties → Events list uses the correct **OnGotFocus** spelling instead of **OnGetFocus**. Existing forms containing the older name retain their bound procedures and are migrated when read/written. Empty Procedure cells suggest `<ComponentName>_onClick`, `<ComponentName>_onGotFocus`, etc., without replacing user-entered names. Double-clicking an empty cell accepts its suggestion, binds `CLASS::<ProcedureName>` to that event, enables navigation, and opens or creates the target event procedure as appropriate. Tests cover migration and UI bindings.
