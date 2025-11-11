package jpamb.sqli;

public class SQLi_SplitJoin {
    // VULNERABLE
    public static void vulnerable(String input) {
        String[] parts = input.split(",");
        String first = parts.length > 0 ? parts[0] : "";
        String query = "SELECT * FROM users WHERE id = " + first;
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String value = "42,43,44";
        String[] parts = value.split(",");
        String first = parts[0];
        String query = "SELECT * FROM users WHERE id = " + first;
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
