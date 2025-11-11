package jpamb.sqli;

public class SQLi_Substring {
    // VULNERABLE
    public static void vulnerable(String input) {
        String trimmed = input.substring(0, Math.min(10, input.length()));
        String query = "SELECT * FROM users WHERE name = '" + trimmed + "'";
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String safe = "safe_value_here";
        String trimmed = safe.substring(0, 4);
        String query = "SELECT * FROM users WHERE name = '" + trimmed + "'";
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
