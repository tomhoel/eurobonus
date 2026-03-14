import { Resend } from "resend";

function getResend() {
  return new Resend(process.env.RESEND_API_KEY);
}

export async function sendAlertEmail(options: {
  to: string;
  origin: string;
  originName: string;
  destination: string;
  destinationName: string;
  date: string;
  cabinClass: string;
  seats: number;
}) {
  const bookingUrl = `https://www.sas.no/book/flights/?search=OW_${options.origin}-${options.destination}-${options.date.replace(/-/g, "")}_a1c0i0y0&bookingFlow=points`;

  const resend = getResend();
  await resend.emails.send({
    from: "Award Finder <alerts@yourdomain.com>",
    to: options.to,
    subject: `${options.cabinClass} bonus seats: ${options.originName} → ${options.destinationName}, ${options.date}`,
    html: `
      <h2>${options.originName} → ${options.destinationName}</h2>
      <p><strong>${options.seats}</strong> ${options.cabinClass} bonus seats on <strong>${options.date}</strong></p>
      <p><a href="${bookingUrl}" style="background:#6366f1;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block">Book on SAS</a></p>
      <p style="color:#999;font-size:12px">You're getting this because you have an alert set for this route.</p>
    `,
  });
}
