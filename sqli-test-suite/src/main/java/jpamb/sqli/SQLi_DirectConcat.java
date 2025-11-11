package jpamb.sqli;

public class SQLi_DirectConcat {
    // VULNERABLE - Should detect SQL injection
    public static void vulnerable(String userId) {
        String query = "SELECT * FROM users WHERE id = " + userId;
        executeQuery(query);
    }
    
    // SAFE - Should NOT flag
    public static void safe() {
        String query = "SELECT * FROM users WHERE id = 42";
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
