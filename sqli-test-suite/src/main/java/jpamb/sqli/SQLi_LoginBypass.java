package jpamb.sqli;

public class SQLi_LoginBypass {
    // VULNERABLE
    public static void vulnerable(String username, String password) {
        String query = "SELECT * FROM users WHERE username = '" + username + 
                       "' AND password = '" + password + "'";
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String username = "admin";
        String password = "secret123";
        String query = "SELECT * FROM users WHERE username = '" + username + 
                       "' AND password = '" + password + "'";
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
