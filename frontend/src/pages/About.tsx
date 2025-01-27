import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

const About = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <Card className="animate-fadeIn">
        <CardHeader>
          <CardTitle className="text-3xl font-bold">About CertiPro</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-gray max-w-none">
          <p className="text-lg text-muted-foreground">
            CertiPro is a comprehensive certification management platform designed to streamline the processes involved in managing ISO standards, conducting audits, and issuing certifications.
          </p>
          <p className="mt-4 text-muted-foreground">
            Our platform serves both certification body employees and organization employees, providing tools for efficient audit management, certification tracking, and compliance monitoring.
          </p>
          <p className="mt-4 text-muted-foreground">
            Whether you're a certification body looking to manage your certification processes or an organization seeking ISO certification, CertiPro provides the tools and features you need to succeed.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default About;