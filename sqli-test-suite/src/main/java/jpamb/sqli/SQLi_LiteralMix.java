package jpamb.sqli;

public class SQLi_LiteralMix {
    // VULNERABLE
    public static void vulnerable(String input) {
        String prefix = "SELECT * FROM ";
        String tableName = "users WHERE name = '" + input + "'";
        String query = prefix + tableName;
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String prefix = "SELECT * FROM ";
        String tableName = "users WHERE id = 1";
        String query = prefix + tableName;
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
