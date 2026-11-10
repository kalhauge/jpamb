package jpamb.utils;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

// Database fixtures for the Jdbc cases. Each call opens a fresh in-memory H2 database.
// The schemas are public so an analysis can read them from the bytecode.
public final class Db {
  private Db() {}

  // A missing driver throws IllegalStateException, not SQLException,
  // so it cannot pass for a "sql error".
  private static Connection connect() throws SQLException {
    try {
      Class.forName("org.h2.Driver");
    } catch (ClassNotFoundException e) {
      throw new IllegalStateException("H2 not on the classpath; run uv run jpamb build", e);
    }
    return DriverManager.getConnection("jdbc:h2:mem:");
  }

  // Coupon 0 means "no coupon".
  public static final String ORDERS = "CREATE TABLE orders(id INT PRIMARY KEY, coupon INT)";

  // Preloaded with users 1, 2 and 3.
  public static final String USERS =
      "CREATE TABLE users(id INT PRIMARY KEY, name VARCHAR(40) NOT NULL, age INT)";

  public static Connection withOrdersTable() throws SQLException {
    Connection conn = connect();
    try (Statement st = conn.createStatement()) {
      st.executeUpdate(ORDERS);
    }
    return conn;
  }

  public static Connection withUsersTable() throws SQLException {
    Connection conn = connect();
    try (Statement st = conn.createStatement()) {
      st.executeUpdate(USERS);
      st.executeUpdate("INSERT INTO users(id, name, age) VALUES (1, 'alice', 30)");
      st.executeUpdate("INSERT INTO users(id, name, age) VALUES (2, 'bob', 25)");
      st.executeUpdate("INSERT INTO users(id, name, age) VALUES (3, 'carol', 41)");
    }
    return conn;
  }

  // Number of rows in the table.
  public static int count(Connection conn, String table) throws SQLException {
    try (Statement st = conn.createStatement();
        ResultSet rs = st.executeQuery(new StringBuilder("SELECT COUNT(*) FROM ").append(table).toString())) {
      rs.next();
      return rs.getInt(1);
    }
  }

  // The coupon stored for order id, or -1 if there is no such order.
  public static int couponOf(Connection conn, int id) throws SQLException {
    try (PreparedStatement ps = conn.prepareStatement("SELECT coupon FROM orders WHERE id = ?")) {
      ps.setInt(1, id);
      try (ResultSet rs = ps.executeQuery()) {
        return rs.next() ? rs.getInt(1) : -1;
      }
    }
  }

  // Checks that order i exists and has coupon coupons[i], for every i.
  public static boolean couponsMatch(Connection conn, int[] coupons) throws SQLException {
    if (count(conn, "orders") != coupons.length) return false;
    for (int i = 0; i < coupons.length; i++) {
      if (couponOf(conn, i) != coupons[i]) return false;
    }
    return true;
  }
}
