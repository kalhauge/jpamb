package jpamb.sqli;

public class SQLi_OrderBy {
    // VULNERABLE
    public static void vulnerable(String sortColumn) {
        String query = "SELECT * FROM products ORDER BY " + sortColumn;
        executeQuery(query);
    }
    
    // SAFE
    public static void safe(String sortColumn) {
        String column = sortColumn.equals("price") ? "price" : "name";
        String query = "SELECT * FROM products ORDER BY " + column;
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
