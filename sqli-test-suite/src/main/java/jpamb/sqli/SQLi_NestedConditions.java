package jpamb.sqli;

public class SQLi_NestedConditions {
    // VULNERABLE
    public static void vulnerable(String input, boolean a, boolean b) {
        String query = "SELECT * FROM users WHERE ";
        if (a) {
            if (b) {
                query += "id = " + input;
            } else {
                query += "name = '" + input + "'";
            }
        } else {
            query += "email = '" + input + "'";
        }
        executeQuery(query);
    }
    
    // SAFE
    public static void safe(boolean a, boolean b) {
        String query = "SELECT * FROM users WHERE ";
        if (a) {
            if (b) {
                query += "id = 42";
            } else {
                query += "name = 'admin'";
            }
        } else {
            query += "email = 'test@example.com'";
        }
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
