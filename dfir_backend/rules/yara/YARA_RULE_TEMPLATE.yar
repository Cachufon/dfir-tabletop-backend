// Update the rule name to something meaningful.
// Add realistic meta fields and strings/conditions.
// Ensure rules remain compatible with standard YARA engines.

rule EXAMPLE_YARA_TEMPLATE
{
    meta:
        description = "Short description of what this YARA rule detects."
        author = "Gruve DFIR"
        reference = "Internal"
        date = "2025-01-01"
        version = "1.0"

    strings:
        $example_string = "example"

    condition:
        $example_string
}
