package jpamb.sqli;

public class SQLi_PartialSanitization {
    // VULNERABLE
    public static void vulnerable(String input) {
        String escaped = input.replace("'", "\\'");
        String query = "SELECT * FROM users WHERE name = '" + escaped + "'";
        executeQuery(query);
    }
    
    // SAFE
    public static void safe(String input) {
        String sanitized = input.replaceAll("[^a-zA-Z0-9]", "");
        String query = "SELECT * FROM users WHERE name = '" + sanitized + "'";
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
