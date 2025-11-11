package jpamb.sqli;

public class SQLi_TimeBased {
    // VULNERABLE
    public static void vulnerable(String userId) {
        String query = "SELECT * FROM users WHERE id = " + userId;
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String userId = "42";
        String query = "SELECT * FROM users WHERE id = " + userId;
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
