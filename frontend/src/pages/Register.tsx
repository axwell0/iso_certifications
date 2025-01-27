// src/pages/Register.tsx
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { Loader2 } from "lucide-react";
import { Button } from "../components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "../components/ui/form";
import { Input } from "../components/ui/input";
import { Link, useSearchParams } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";

const formSchema = z.object({
  full_name: z.string().min(2, "Full name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  token: z.string().optional(),
});

const Register = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isRegistered, setIsRegistered] = useState(false);
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const invitationToken = searchParams.get('token');
  const invitationEmail = searchParams.get('email');

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      full_name: "",
      email: invitationEmail || "",
      password: "",
      token: invitationToken || undefined,
    },
  });

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      setIsLoading(true);
      const payload = {
        ...values,
        ...(invitationToken && { token: invitationToken })
      };

      const response = await fetch("https://127.0.0.1:5000/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        let errorMessage = "Registration failed";

        if (errorData.error?.toLowerCase().includes("already exists")) {
          errorMessage = "This email is already registered. Please sign in.";
        } else if (errorData.error) {
          errorMessage = errorData.error;
        }

        toast({
          title: "Registration failed",
          description: errorMessage,
          variant: "destructive",
        });
        return;
      }

      const data = await response.json();
      setIsRegistered(true);
      toast({
        title: "Registration successful",
        description: invitationToken
          ? "You've successfully joined the organization!"
          : "Account created successfully!",
      });

    } catch (error) {
      toast({
        title: "Error",
        description: "Please try again later.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted">
      <div className="w-full max-w-md space-y-8 p-8 bg-background rounded-lg shadow-lg animate-fadeIn">
        {isRegistered ? (
          <div className="space-y-6 text-center">
            <h2 className="text-2xl font-bold text-primary">Registration Successful!</h2>
            <p className="mt-2 text-muted-foreground">
              {invitationToken ? "You've successfully joined the organization!" : "Welcome to CertiPro!"}
            </p>
            <Button asChild>
              <Link to="/login">Continue to Login</Link>
            </Button>
          </div>
        ) : (
          <>
            <div className="text-center">
              <h2 className="text-2xl font-bold text-primary">
                {invitationToken ? "Join Organization" : "Create Account"}
              </h2>
              <p className="mt-2 text-muted-foreground">
                {invitationToken
                  ? "Complete registration to join the organization"
                  : "Sign up to get started with CertiPro"}
              </p>
            </div>

            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="full_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Full Name</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Enter your full name"
                          {...field}
                          disabled={isLoading}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input
                          type="email"
                          placeholder="Enter your email"
                          {...field}
                          disabled={isLoading || !!invitationEmail}
                          className={invitationEmail ? "bg-muted/50" : ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Password</FormLabel>
                      <FormControl>
                        <Input
                          type="password"
                          placeholder="Create a password"
                          {...field}
                          disabled={isLoading}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Processing...</span>
                    </div>
                  ) : (
                    "Sign up"
                  )}
                </Button>
              </form>
            </Form>

            <div className="text-center text-sm">
              <span className="text-muted-foreground">Already have an account? </span>
              <Link
                to="/login"
                className="font-medium text-primary hover:text-primary/80"
              >
                Sign in
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Register;