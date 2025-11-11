package jpamb.sqli;

public class SQLi_TryCatch {
    // VULNERABLE
    public static void vulnerable(String input) {
        String query;
        try {
            query = "SELECT * FROM users WHERE id = " + input;
            executeQuery(query);
        } catch (Exception e) {
            query = "SELECT * FROM default WHERE id = " + input;
            executeQuery(query);
        }
    }
    
    // SAFE
    public static void safe() {
        String query;
        try {
            query = "SELECT * FROM users WHERE id = 42";
            executeQuery(query);
        } catch (Exception e) {
            query = "SELECT * FROM default WHERE id = 1";
            executeQuery(query);
        }
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
