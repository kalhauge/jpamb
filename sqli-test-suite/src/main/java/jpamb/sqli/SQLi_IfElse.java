package jpamb.sqli;

public class SQLi_IfElse {
    // VULNERABLE
    public static void vulnerable(String input, boolean condition) {
        String query;
        if (condition) {
            query = "SELECT * FROM users WHERE id = " + input;
        } else {
            query = "SELECT * FROM admins WHERE id = " + input;
        }
        executeQuery(query);
    }
    
    // SAFE
    public static void safe(boolean condition) {
        String query;
        if (condition) {
            query = "SELECT * FROM users WHERE id = 42";
        } else {
            query = "SELECT * FROM users WHERE id = 43";
        }
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
