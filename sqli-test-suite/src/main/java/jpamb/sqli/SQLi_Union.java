package jpamb.sqli;

public class SQLi_Union {
    // VULNERABLE
    public static void vulnerable(String productId) {
        String query = "SELECT name, price FROM products WHERE id = " + productId;
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String productId = "42";
        String query = "SELECT name, price FROM products WHERE id = " + productId;
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
