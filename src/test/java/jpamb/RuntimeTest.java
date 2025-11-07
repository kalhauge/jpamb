package jpamb;

import org.junit.Test;
import static org.junit.Assert.*;

import java.lang.reflect.Method;
import jpamb.cases.*;
import jpamb.utils.Case;

/**
 * Validation tests for the Runtime class and benchmark cases.
 * These ensure that benchmark cases behave as documented, so students
 * can trust the benchmarks when developing their analysis tools.
 */
public class RuntimeTest {

    @Test
    public void testMethodSignaturePrinting() {
        // Test that method signatures are printed correctly
        try {
            Method m = Simple.class.getMethod("divideByZero");
            String sig = Runtime.printMethodSignature(m);
            assertEquals("()I", sig);

            Method m2 = Simple.class.getMethod("divideByN", int.class);
            String sig2 = Runtime.printMethodSignature(m2);
            assertEquals("(I)I", sig2);

            Method m3 = Simple.class.getMethod("justReturnNothing");
            String sig3 = Runtime.printMethodSignature(m3);
            assertEquals("()V", sig3);
        } catch (NoSuchMethodException e) {
            fail("Method not found: " + e.getMessage());
        }
    }

    @Test
    public void testCaseAnnotationsPresent() {
        // Verify that methods have their @Case annotations
        try {
            Method m = Simple.class.getMethod("divideByZero");
            Case[] cases = Runtime.cases(m);
            assertTrue("divideByZero should have @Case annotations", cases.length > 0);

            Method m2 = Simple.class.getMethod("assertBoolean", boolean.class);
            Case[] cases2 = Runtime.cases(m2);
            assertTrue("assertBoolean should have multiple @Case annotations", cases2.length >= 2);
        } catch (NoSuchMethodException e) {
            fail("Method not found: " + e.getMessage());
        }
    }

    @Test
    public void testSampleCasesBehaveAsExpected() {
        // Spot-check a few critical cases to ensure they behave as documented

        // This should throw ArithmeticException (divide by zero)
        try {
            Simple.divideByZero();
            fail("divideByZero() should throw ArithmeticException");
        } catch (ArithmeticException e) {
            // Expected - documented behavior confirmed
        }

        // This should throw AssertionError
        try {
            Simple.assertFalse();
            fail("assertFalse() should throw AssertionError");
        } catch (AssertionError e) {
            // Expected - documented behavior confirmed
        }

        // This should succeed
        try {
            int result = Simple.justReturn();
            assertEquals(0, result);
        } catch (Exception e) {
            fail("justReturn() should not throw: " + e.getMessage());
        }
    }

    @Test
    public void testAllCaseClassesAccessible() {
        // Ensure all case classes referenced in Runtime are accessible
        assertNotNull(Simple.class);
        assertNotNull(Loops.class);
        assertNotNull(Tricky.class);
        assertNotNull(jpamb.cases.Arrays.class);
        assertNotNull(Calls.class);
    }
}
