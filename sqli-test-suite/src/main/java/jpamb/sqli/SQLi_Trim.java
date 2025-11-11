package jpamb.sqli;

public class SQLi_Trim {
    // VULNERABLE
    public static void vulnerable(String input) {
        String cleaned = input.trim();
        String query = "SELECT * FROM users WHERE id = " + cleaned;
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String value = "  42  ";
        String cleaned = value.trim();
        String query = "SELECT * FROM users WHERE id = " + cleaned;
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
