package jpamb.sqli;

public class SQLi_CaseConversion {
    // VULNERABLE
    public static void vulnerable(String input) {
        String upper = input.toUpperCase();
        String query = "SELECT * FROM users WHERE name = '" + upper + "'";
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String value = "admin";
        String upper = value.toUpperCase();
        String query = "SELECT * FROM users WHERE role = '" + upper + "'";
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
