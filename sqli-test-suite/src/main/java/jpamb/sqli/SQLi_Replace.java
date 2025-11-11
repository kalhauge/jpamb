package jpamb.sqli;

public class SQLi_Replace {
    // VULNERABLE
    public static void vulnerable(String input) {
        String escaped = input.replace("'", "''");
        String query = "SELECT * FROM users WHERE name = '" + escaped + "'";
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String base = "SELECT * FROM table_name WHERE x = y";
        String query = base.replace("table_name", "users");
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
