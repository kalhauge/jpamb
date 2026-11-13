package jpamb.cases;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import jpamb.utils.Case;
import jpamb.utils.Db;

// JDBC cases. Each method gets a fresh in-memory database from Db.
// A thrown SQLException is "sql error". Wrong data in the database fails an assert.
// Strings are built with StringBuilder instead of + to avoid invokedynamic.
public class Jdbc {

  static final String INSERT_ORDER = "INSERT INTO orders(id, coupon) VALUES (?, ?)";

  // Bindings in loops

  // The coupon is only bound when it is not 0, so later orders reuse the last one.
  @Case("([I: 0]) -> sql error")
  @Case("([I: 7, 0]) -> assertion error")
  @Case("([I: 7, 7]) -> ok")
  @Case("([I: ]) -> ok")
  public static void insertOrders(int[] coupons) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    for (int i = 0; i < coupons.length; i++) {
      ps.setInt(1, i);
      if (coupons[i] != 0) {
        ps.setInt(2, coupons[i]);
      }
      ps.addBatch();
    }
    ps.executeBatch();
    assert Db.couponsMatch(conn, coupons);
  }

  // Fixed: both parameters are bound on every iteration.
  @Case("([I: 0]) -> ok")
  @Case("([I: 7, 0]) -> ok")
  @Case("([I: 0, 7]) -> ok")
  public static void insertOrdersBindEveryIteration(int[] coupons) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    for (int i = 0; i < coupons.length; i++) {
      ps.setInt(1, i);
      ps.setInt(2, coupons[i]);
      ps.addBatch();
    }
    ps.executeBatch();
    assert Db.couponsMatch(conn, coupons);
  }

  // clearParameters after addBatch turns the reuse into a missing binding.
  @Case("([I: 7, 0]) -> sql error")
  @Case("([I: 7, 7]) -> ok")
  @Case("([I: ]) -> ok")
  public static void insertOrdersClearAfterAdd(int[] coupons) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    for (int i = 0; i < coupons.length; i++) {
      ps.setInt(1, i);
      if (coupons[i] != 0) {
        ps.setInt(2, coupons[i]);
      }
      ps.addBatch();
      ps.clearParameters();
    }
    ps.executeBatch();
    assert Db.couponsMatch(conn, coupons);
  }

  // The coupon is bound once before the loop and reused on purpose.
  @Case("([I: 1, 2], 5) -> ok")
  @Case("([I: ], 5) -> ok")
  @Case("([I: 1, 1], 5) -> sql error")
  public static void insertOrdersSharedCoupon(int[] ids, int coupon) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    ps.setInt(2, coupon);
    for (int i = 0; i < ids.length; i++) {
      ps.setInt(1, ids[i]);
      ps.executeUpdate();
    }
    assert Db.count(conn, "orders") == ids.length;
  }

  // The default coupon is only bound when useDefault is true.
  @Case("(true, 2) -> ok")
  @Case("(false, 1) -> sql error")
  @Case("(false, 0) -> ok")
  public static void insertDefaultOnOneBranch(boolean useDefault, int n) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    if (useDefault) {
      ps.setInt(2, 0);
    }
    for (int i = 0; i < n; i++) {
      ps.setInt(1, i);
      ps.executeUpdate();
    }
  }

  // Helpers and aliases

  static void bindCoupon(PreparedStatement ps, int coupon) throws SQLException {
    if (coupon != 0) {
      ps.setInt(2, coupon);
    }
  }

  // The helper skips the binding for coupon 0.
  @Case("(0) -> sql error")
  @Case("(5) -> ok")
  public static void bindCouponInHelper(int coupon) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    ps.setInt(1, 1);
    bindCoupon(ps, coupon);
    ps.executeUpdate();
  }

  // Binding through an alias binds the same statement.
  @Case("(0) -> ok")
  @Case("(3) -> ok")
  public static void aliasedStatement(int coupon) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    PreparedStatement alias = ps;
    alias.setInt(1, 1);
    alias.setInt(2, coupon);
    ps.executeUpdate();
    assert Db.couponOf(conn, 1) == coupon;
  }

  // For coupon 0 the lookup statement is bound instead of the insert.
  @Case("(4) -> ok")
  @Case("(0) -> sql error")
  public static void bindsWrongStatementOnOneBranch(int coupon) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement insert = conn.prepareStatement(INSERT_ORDER);
    PreparedStatement lookup = conn.prepareStatement("SELECT coupon FROM orders WHERE id = ?");
    insert.setInt(1, 1);
    if (coupon > 0) {
      insert.setInt(2, coupon);
    } else {
      lookup.setInt(1, 0);
    }
    insert.executeUpdate();
  }

  // Statement lifecycle

  // Executes a statement that may already be closed.
  @Case("(true) -> sql error")
  @Case("(false) -> ok")
  public static void executeAfterClose(boolean closeEarly) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    ps.setInt(1, 1);
    ps.setInt(2, 0);
    if (closeEarly) {
      ps.close();
    }
    ps.executeUpdate();
  }

  // Closed inside the loop, so the second iteration fails.
  @Case("(0) -> ok")
  @Case("(1) -> ok")
  @Case("(2) -> sql error")
  public static void closeInsideLoop(int n) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    for (int i = 0; i < n; i++) {
      ps.setInt(1, i);
      ps.setInt(2, 0);
      ps.executeUpdate();
      ps.close();
    }
  }

  // Bindings survive executeBatch, so executing again inserts the same row.
  @Case("(true) -> sql error")
  @Case("(false) -> ok")
  public static void resubmitAfterBatch(boolean resend) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    ps.setInt(1, 1);
    ps.setInt(2, 3);
    ps.addBatch();
    ps.executeBatch();
    if (resend) {
      ps.executeUpdate();
    }
  }

  // The second order reuses the coupon bound before the batch.
  @Case("(0) -> ok")
  @Case("(5) -> assertion error")
  public static void reuseAfterBatch(int coupon) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    ps.setInt(1, 1);
    ps.setInt(2, coupon);
    ps.addBatch();
    ps.executeBatch();
    ps.setInt(1, 2);
    ps.executeUpdate();
    assert Db.couponOf(conn, 2) == 0;
  }

  // Query structure and schema

  // The short query has one parameter, but two are always bound.
  @Case("(true) -> ok")
  @Case("(false) -> sql error")
  public static void queryAlternativesMismatch(boolean withCoupon) throws SQLException {
    Connection conn = Db.withOrdersTable();
    String sql;
    if (withCoupon) {
      sql = INSERT_ORDER;
    } else {
      sql = "INSERT INTO orders(id) VALUES (?)";
    }
    PreparedStatement ps = conn.prepareStatement(sql);
    ps.setInt(1, 1);
    ps.setInt(2, 5);
    ps.executeUpdate();
  }

  // Fixed: the coupon is only bound when the query has it.
  @Case("(true, 5) -> ok")
  @Case("(false, 5) -> ok")
  public static void queryAlternativesMatched(boolean withCoupon, int coupon)
      throws SQLException {
    Connection conn = Db.withOrdersTable();
    String sql;
    if (withCoupon) {
      sql = INSERT_ORDER;
    } else {
      sql = "INSERT INTO orders(id) VALUES (?)";
    }
    PreparedStatement ps = conn.prepareStatement(sql);
    ps.setInt(1, 1);
    if (withCoupon) {
      ps.setInt(2, coupon);
    }
    ps.executeUpdate();
    int expected = 0;
    if (withCoupon) {
      expected = coupon;
    }
    assert Db.couponOf(conn, 1) == expected;
  }

  // A string bound to an INT column fails unless it is a number.
  @Case("(s'7') -> ok")
  @Case("(s'seven') -> sql error")
  public static void couponFromText(String coupon) throws SQLException {
    Connection conn = Db.withOrdersTable();
    PreparedStatement ps = conn.prepareStatement(INSERT_ORDER);
    ps.setInt(1, 1);
    ps.setString(2, coupon);
    ps.executeUpdate();
  }

  // Choice 2 selects a column that does not exist.
  @Case("(0) -> ok")
  @Case("(1) -> ok")
  @Case("(2) -> sql error")
  public static void selectColumnByChoice(int choice) throws SQLException {
    Connection conn = Db.withUsersTable();
    String column;
    if (choice == 0) {
      column = "name";
    } else if (choice == 1) {
      column = "age";
    } else {
      column = "email";
    }
    String sql =
        new StringBuilder("SELECT ").append(column).append(" FROM users WHERE id = ?").toString();
    PreparedStatement ps = conn.prepareStatement(sql);
    ps.setInt(1, 1);
    ResultSet rs = ps.executeQuery();
    boolean found = rs.next();
    assert found;
  }

  // The result of next() is ignored, so a missing user is read anyway.
  @Case("(1) -> ok")
  @Case("(9) -> sql error")
  public static int readAge(int id) throws SQLException {
    Connection conn = Db.withUsersTable();
    PreparedStatement ps = conn.prepareStatement("SELECT age FROM users WHERE id = ?");
    ps.setInt(1, id);
    ResultSet rs = ps.executeQuery();
    rs.next();
    return rs.getInt(1);
  }

  // Building queries

  // Binding starts at the second id, so the first placeholder is never set.
  @Case("([I: ]) -> ok")
  @Case("([I: 1]) -> sql error")
  @Case("([I: 1, 2]) -> sql error")
  public static void orQueryOffByOne(int[] ids) throws SQLException {
    Connection conn = Db.withUsersTable();
    StringBuilder sb = new StringBuilder("SELECT COUNT(*) FROM users");
    for (int i = 0; i < ids.length; i++) {
      if (i == 0) {
        sb.append(" WHERE id = ?");
      } else {
        sb.append(" OR id = ?");
      }
    }
    PreparedStatement ps = conn.prepareStatement(sb.toString());
    for (int i = 1; i < ids.length; i++) {
      ps.setInt(i, ids[i]);
    }
    ResultSet rs = ps.executeQuery();
    rs.next();
  }

  // With no ids there is no WHERE, so every user is counted.
  @Case("([I: ]) -> assertion error")
  @Case("([I: 1, 2]) -> ok")
  @Case("([I: 1, 1, 9]) -> ok")
  public static void orQuery(int[] ids) throws SQLException {
    Connection conn = Db.withUsersTable();
    StringBuilder sb = new StringBuilder("SELECT COUNT(*) FROM users");
    for (int i = 0; i < ids.length; i++) {
      if (i == 0) {
        sb.append(" WHERE id = ?");
      } else {
        sb.append(" OR id = ?");
      }
    }
    PreparedStatement ps = conn.prepareStatement(sb.toString());
    for (int i = 0; i < ids.length; i++) {
      ps.setInt(i + 1, ids[i]);
    }
    ResultSet rs = ps.executeQuery();
    rs.next();
    assert rs.getInt(1) <= ids.length;
  }

  // The input is pasted into the query: SQL injection.
  @Case("(s'1') -> ok")
  @Case("(s'1 OR 1=1') -> assertion error")
  @Case("(s'x') -> sql error")
  public static void countUsersUnsafe(String id) throws SQLException {
    Connection conn = Db.withUsersTable();
    Statement st = conn.createStatement();
    String sql =
        new StringBuilder("SELECT COUNT(*) FROM users WHERE id = ").append(id).toString();
    ResultSet rs = st.executeQuery(sql);
    rs.next();
    assert rs.getInt(1) <= 1;
  }

  // Fixed with a parameter: no injection, but non-numbers fail to convert.
  @Case("(s'1') -> ok")
  @Case("(s'4') -> ok")
  @Case("(s'1 OR 1=1') -> sql error")
  public static void countUsersPrepared(String id) throws SQLException {
    Connection conn = Db.withUsersTable();
    PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM users WHERE id = ?");
    ps.setString(1, id);
    ResultSet rs = ps.executeQuery();
    rs.next();
    assert rs.getInt(1) <= 1;
  }
}
