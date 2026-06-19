/**
 * Typed, validated access to environment variables.
 *
 * Validating at module load fails fast with a clear message if a required
 * variable is missing, instead of surfacing `undefined` deep in the app.
 */
import { z } from "zod";

const clientSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z.string().url(),
});

const serverSchema = z.object({
  API_INTERNAL_BASE_URL: z.string().url(),
});

/** Variables safe to use in the browser (must be `NEXT_PUBLIC_*`). */
export const clientEnv = clientSchema.parse({
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
});

/**
 * Server-only variables. Access this only from Server Components, route
 * handlers, or server actions — never from client code.
 */
export function getServerEnv() {
  return serverSchema.parse({
    API_INTERNAL_BASE_URL: process.env.API_INTERNAL_BASE_URL,
  });
}
