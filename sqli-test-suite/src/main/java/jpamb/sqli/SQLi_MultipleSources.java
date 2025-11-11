package jpamb.sqli;

public class SQLi_MultipleSources {
    // VULNERABLE
    public static void vulnerable(String httpInput, String fileInput) {
        String query = "SELECT * FROM users WHERE name = '" + httpInput + 
                       "' OR email = '" + fileInput + "'";
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String httpInput = "admin";
        String fileInput = "admin@example.com";
        String query = "SELECT * FROM users WHERE name = '" + httpInput + 
                       "' OR email = '" + fileInput + "'";
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
