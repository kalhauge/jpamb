package jpamb.sqli;

public class SQLi_HTTPSource {
    // VULNERABLE - Simulates HTTP request parameter
    public static void vulnerable(String requestParam) {
        String userId = requestParam;
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
